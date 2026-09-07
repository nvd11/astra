"""会话与消息路由模块.

提供会话的创建、分页查询、更新、删除，以及消息的历史回溯与编辑.
严格遵循基于 current_user.id 的多租户行级数据隔离.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.configs.config import Settings, get_settings
from src.engine.mysql_client import get_db_session
from src.memory.short_term import get_short_term_memory
from src.models.conversation import ConversationRepository, MessageRepository
from src.models.requests import (
    CreateConversationRequest,
    EditMessageRequest,
    UpdateConversationRequest,
)
from src.models.responses import (
    BaseResponse,
    ConversationData,
    ConversationListResponse,
    ConversationResponse,
    MessageData,
    MessageListResponse,
    MessageResponse,
    PaginatedData,
)
from src.models.user import User
from src.services.auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建新会话",
    description="创建新的对话 Session，支持绑定指定模型与智能体偏好",
)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session_id: Annotated[
        str | None,
        Header(alias="X-Session-ID", description="可选设备会话ID"),
    ] = None,
) -> ConversationResponse:
    """创建新会话端点."""
    repo = ConversationRepository(db)

    # 确定模型与 Agent 偏好（优先请求参数，其次用户偏好，最后系统默认）
    model = (
        request.model
        or getattr(current_user, "default_model", None)
        or settings.default_model
    )
    agent = (
        request.agent_preference
        or getattr(current_user, "default_agent", None)
        or "auto"
    )
    title = request.title or "新对话"

    conversation = await repo.create(
        user_id=current_user.id,
        session_id=session_id,
        title=title,
        model=model,
        agent_preference=agent,
        system_prompt=request.system_prompt,
    )

    logger.info(
        f"Created conversation id={conversation.id} user={current_user.username}"
    )

    return ConversationResponse(
        code=0,
        message="success",
        data=ConversationData(
            id=conversation.id,
            session_id=conversation.session_id,
            title=conversation.title,
            model=conversation.model,
            agent_preference=conversation.agent_preference,
            system_prompt=conversation.system_prompt,
            is_archived=conversation.is_archived,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=0,
        ),
    )


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="分页获取会话列表",
    description="获取当前用户的会话列表，支持按归档状态过滤，按更新时间倒序",
)
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页大小")] = 20,
    is_archived: Annotated[bool | None, Query(description="归档状态过滤")] = False,
) -> ConversationListResponse:
    """分页获取用户的会话列表."""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)

    items, total = await conv_repo.list_by_user(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        is_archived=is_archived,
    )

    # 组装返回数据，附带每条会话的消息数量
    conversation_items: list[ConversationData] = []
    for conv in items:
        msg_count = await msg_repo.get_message_count(conv.id, current_user.id)
        conversation_items.append(
            ConversationData(
                id=conv.id,
                session_id=conv.session_id,
                title=conv.title,
                model=conv.model,
                agent_preference=conv.agent_preference,
                system_prompt=conv.system_prompt,
                is_archived=conv.is_archived,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=msg_count,
            )
        )

    has_more = (page * page_size) < total

    return ConversationListResponse(
        code=0,
        message="success",
        data=PaginatedData(
            items=conversation_items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        ),
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="获取单个会话详情",
    description="获取单个会话的元数据，强制多租户行级隔离",
)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversationResponse:
    """获取单个会话元数据."""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)

    conversation = await conv_repo.get_by_id(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    msg_count = await msg_repo.get_message_count(conversation.id, current_user.id)

    return ConversationResponse(
        code=0,
        message="success",
        data=ConversationData(
            id=conversation.id,
            session_id=conversation.session_id,
            title=conversation.title,
            model=conversation.model,
            agent_preference=conversation.agent_preference,
            system_prompt=conversation.system_prompt,
            is_archived=conversation.is_archived,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=msg_count,
        ),
    )


@router.put(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="修改会话信息",
    description="更新会话标题、模型偏好、系统提示词或归档状态",
)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversationResponse:
    """更新会话属性."""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)

    update_fields = request.model_dump(exclude_unset=True)
    updated = await conv_repo.update(conversation_id, current_user.id, **update_fields)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    msg_count = await msg_repo.get_message_count(updated.id, current_user.id)

    logger.info(f"Updated conversation {conversation_id} user={current_user.username}")

    return ConversationResponse(
        code=0,
        message="success",
        data=ConversationData(
            id=updated.id,
            session_id=updated.session_id,
            title=updated.title,
            model=updated.model,
            agent_preference=updated.agent_preference,
            system_prompt=updated.system_prompt,
            is_archived=updated.is_archived,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
            message_count=msg_count,
        ),
    )


@router.delete(
    "/{conversation_id}",
    response_model=BaseResponse[dict[str, Any]],
    summary="删除会话",
    description="彻底删除会话及其关联的所有消息",
)
async def delete_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[dict[str, Any]]:
    """删除会话."""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)

    # 检查是否存在
    conv = await conv_repo.get_by_id(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # 级联删除/软删除消息
    await msg_repo.delete_by_conversation(conversation_id, current_user.id)
    # 删除会话实体
    await conv_repo.delete(conversation_id, current_user.id)
    # 清理该会话的 L1 Redis 缓存
    await get_short_term_memory().clear(conversation_id)

    logger.info(f"Deleted conversation {conversation_id} user={current_user.username}")

    return BaseResponse(
        code=0,
        message="success",
        data={"deleted": True, "id": conversation_id},
    )


# ========================== 消息子路由 ==========================


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
    summary="获取会话历史消息",
    description="分页拉取指定会话下的消息明细，按发送时间升序排列",
)
async def list_messages(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=200, description="每页消息数")] = 50,
) -> MessageListResponse:
    """获取会话的历史消息."""
    conv_repo = ConversationRepository(db)
    # 强制行级隔离：检查会话归属
    conv = await conv_repo.get_by_id(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    msg_repo = MessageRepository(db)
    items, total = await msg_repo.list_by_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    data_items = [
        MessageData(
            id=m.id,
            conversation_id=m.conversation_id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            metadata=m.message_metadata,
            tokens_used=m.tokens_used,
            created_at=m.created_at,
        )
        for m in items
    ]

    has_more = (page * page_size) < total

    return MessageListResponse(
        code=0,
        message="success",
        data=PaginatedData(
            items=data_items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        ),
    )


@router.put(
    "/{conversation_id}/messages/{message_id}",
    response_model=MessageResponse,
    summary="编辑单条消息",
    description="修改单条已发送消息内容（通常用于重新发起分支对话）",
)
async def edit_message(
    conversation_id: str,
    message_id: str,
    request: EditMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MessageResponse:
    """编辑历史消息内容."""
    conv_repo = ConversationRepository(db)
    conv = await conv_repo.get_by_id(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    msg_repo = MessageRepository(db)
    msg = await msg_repo.get_by_id(message_id, current_user.id)
    if not msg or msg.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    updated_msg = await msg_repo.update_content(
        message_id, current_user.id, request.content
    )
    if not updated_msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message update failed",
        )

    # 消息修改后清除该会话的 L1 缓存，确保下一轮提问从 MySQL 获取最新上下文
    await get_short_term_memory().clear(conversation_id)

    return MessageResponse(
        code=0,
        message="success",
        data=MessageData(
            id=updated_msg.id,
            conversation_id=updated_msg.conversation_id,
            session_id=updated_msg.session_id,
            role=updated_msg.role,
            content=updated_msg.content,
            metadata=updated_msg.message_metadata,
            tokens_used=updated_msg.tokens_used,
            created_at=updated_msg.created_at,
        ),
    )


@router.delete(
    "/{conversation_id}/messages/{message_id}",
    response_model=BaseResponse[dict[str, Any]],
    summary="删除单条消息",
    description="软删除指定单条消息",
)
async def delete_message(
    conversation_id: str,
    message_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[dict[str, Any]]:
    """软删除单条消息."""
    conv_repo = ConversationRepository(db)
    conv = await conv_repo.get_by_id(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    msg_repo = MessageRepository(db)
    msg = await msg_repo.get_by_id(message_id, current_user.id)
    if not msg or msg.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    await msg_repo.soft_delete(message_id, current_user.id)
    # 消息软删除后失效 L1 缓存
    await get_short_term_memory().clear(conversation_id)

    return BaseResponse(
        code=0,
        message="success",
        data={"deleted": True, "message_id": message_id},
    )
