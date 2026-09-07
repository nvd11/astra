"""LLM 推理与 SSE 流式输出路由模块.

支持私有 LiteLLM 网关流式输出、打字机效果推送、消息入库及手动中止推理.
"""

import contextlib
import json
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.graph import astream_chat
from src.configs.config import Settings, get_settings
from src.engine.mysql_client import get_db_session, get_mysql_client
from src.engine.redis_client import get_redis_client
from src.memory.short_term import get_short_term_memory
from src.models.conversation import ConversationRepository, MessageRepository
from src.models.requests import SendMessageRequest, StopChatRequest
from src.models.responses import BaseResponse, ChatStreamChunkData
from src.models.user import User
from src.services.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/stream",
    summary="SSE 流式对话补全",
    description="发送对话消息并以 Server-Sent Events (SSE) 协议实时流式输出推理内容",
)
async def chat_stream(
    request: SendMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session_id: Annotated[
        str | None,
        Header(alias="X-Session-ID", description="可选设备会话ID"),
    ] = None,
) -> StreamingResponse:
    """SSE 流式对话补全端点."""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)

    # 1. 验证会话存在且属于当前用户 (严格行级隔离)
    conv = await conv_repo.get_by_id(request.conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # 2. 保存用户消息到数据库 (附加设备 session_id 审计溯源)
    user_msg = await msg_repo.create(
        conversation_id=conv.id,
        user_id=current_user.id,
        session_id=session_id,
        role="user",
        content=request.content,
    )
    logger.info(f"Saved user message id={user_msg.id} for conv={conv.id}")

    # 3. 构建多轮上下文：优先读 L1 Redis 缓存加速；未命中穿透至 MySQL 并回填 Redis
    memory = get_short_term_memory()
    cached_context = await memory.get_context(conv.id)
    if cached_context is not None:
        cached_context.append({"role": "user", "content": request.content})
        llm_context = cached_context[-20:]
        await memory.set_context(conv.id, llm_context)
    else:
        history_messages = await msg_repo.get_recent_messages(
            conversation_id=conv.id,
            user_id=current_user.id,
            limit=20,
        )
        llm_context = [{"role": m.role, "content": m.content} for m in history_messages]
        await memory.set_context(conv.id, llm_context)

    # 确定模型与 Agent 偏好
    model = request.model_override or conv.model or settings.default_model
    agent = request.agent_override or conv.agent_preference or "auto"
    conversation_id = conv.id
    user_id = current_user.id
    msg_id = str(uuid.uuid4())

    redis_client = get_redis_client()
    stop_key = f"chat:stop:{conversation_id}"

    async def check_is_stopped() -> bool:
        """检查是否有中止推理信号."""
        try:
            val = await redis_client.get(stop_key)
            return val is not None and val != ""
        except Exception as err:
            logger.warning(f"Error checking redis stop key: {err}")
            return False

    async def event_generator() -> AsyncIterator[str]:
        """SSE 数据生成器."""
        collected_chunks: list[str] = []
        final_model = model
        final_agent = agent
        finish_reason = None

        try:
            stream = astream_chat(
                messages=llm_context,
                model=model,
                agent_preference=agent,
                system_prompt=conv.system_prompt,
                stop_checker=check_is_stopped,
            )

            async for chunk in stream:
                delta = chunk.get("delta", "")
                if delta:
                    collected_chunks.append(delta)

                chunk_finish_reason = chunk.get("finish_reason")
                if chunk_finish_reason:
                    finish_reason = chunk_finish_reason

                final_model = chunk.get("model", final_model)
                final_agent = chunk.get("agent", final_agent)

                chunk_payload = ChatStreamChunkData(
                    id=msg_id,
                    delta=delta,
                    finish_reason=chunk_finish_reason,
                    model=final_model,
                    agent=final_agent,
                )

                yield f"data: {chunk_payload.model_dump_json()}\n\n"

            # 发送 [DONE] 结束标记
            yield "data: [DONE]\n\n"

        except Exception as exc:
            logger.error(f"Error in chat stream generation: {exc}")
            err_payload = {
                "error": True,
                "message": str(exc),
            }
            yield f"data: {json.dumps(err_payload)}\n\n"
        finally:
            # 清理 Redis 中止标志
            with contextlib.suppress(Exception):
                await redis_client.delete(stop_key)

            # 4. 流式结束：开启新的独立 session 将 Assistant 消息持久化入库，并追加 L1 缓存
            full_response_text = "".join(collected_chunks)
            if full_response_text:
                # 顺手将 Assistant 回复写入 L1 会话缓存
                await memory.append_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response_text,
                )

                try:
                    mysql = get_mysql_client()
                    async with mysql.session_scope() as session:
                        persist_msg_repo = MessageRepository(session)
                        persist_conv_repo = ConversationRepository(session)

                        await persist_msg_repo.create(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            session_id=session_id,
                            role="assistant",
                            content=full_response_text,
                            metadata={
                                "agent": final_agent,
                                "finish_reason": finish_reason,
                            },
                        )

                        # 刷新会话更新时间
                        await persist_conv_repo.update(
                            conversation_id=conversation_id,
                            user_id=user_id,
                        )
                        logger.info(
                            f"Persisted assistant message for conv={conversation_id}, length={len(full_response_text)}"
                        )
                except Exception as save_err:
                    logger.error(f"Failed to persist assistant message: {save_err}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/stop",
    response_model=BaseResponse[dict[str, Any]],
    summary="手动中止推理",
    description="向当前进行中的推理任务发送停止信号，后端将在下一 Token 时优雅中断",
)
async def stop_chat(
    request: StopChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[dict[str, Any]]:
    """手动中止推理端点."""
    conv_repo = ConversationRepository(db)

    # 验证会话存在且属于该用户
    conv = await conv_repo.get_by_id(request.conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    redis_client = get_redis_client()
    stop_key = f"chat:stop:{conv.id}"
    await redis_client.setex(stop_key, 60, "1")

    logger.info(
        f"Stop signal set for conversation {conv.id} by user {current_user.username}"
    )

    return BaseResponse(
        code=0,
        message="Inference stop signal sent",
        data={"conversation_id": conv.id, "stopped": True},
    )
