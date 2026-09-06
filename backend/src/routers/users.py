"""用户资料、偏好与用量统计路由模块.

提供个人资料查询/修改、智能体与模型偏好调整、以及实时 Token 用量统计.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.engine.mysql_client import get_db_session
from src.models.conversation import Conversation, Message
from src.models.requests import UpdatePreferenceRequest, UpdateProfileRequest
from src.models.responses import (
    UsageStatsData,
    UsageStatsResponse,
    UserInfoData,
    UserInfoResponse,
)
from src.models.user import User, UserRepository
from src.services.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserInfoResponse,
    summary="获取个人资料",
    description="获取当前登录用户的核心资料实体与个性化配置",
)
async def get_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserInfoResponse:
    """获取当前登录用户的完整资料."""
    return UserInfoResponse(
        code=0,
        message="success",
        data=UserInfoData(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            avatar_url=current_user.avatar_url,
            preferences=current_user.preferences or {},
            default_model=current_user.default_model,
            default_agent=current_user.default_agent,
            created_at=current_user.created_at,
        ),
    )


@router.put(
    "/me",
    response_model=UserInfoResponse,
    summary="修改个人资料",
    description="更新当前用户的头像 URL 或通用 preferences 字典",
)
async def update_user_profile(
    request: UpdateProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserInfoResponse:
    """修改头像和通用偏好."""
    repo = UserRepository(db)

    update_fields = request.model_dump(exclude_unset=True)
    updated_user = await repo.update(current_user.id, **update_fields)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    logger.info(
        f"Updated profile for user id={current_user.id}, fields={list(update_fields.keys())}"
    )

    return UserInfoResponse(
        code=0,
        message="success",
        data=UserInfoData(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            avatar_url=updated_user.avatar_url,
            preferences=updated_user.preferences or {},
            default_model=updated_user.default_model,
            default_agent=updated_user.default_agent,
            created_at=updated_user.created_at,
        ),
    )


@router.put(
    "/preferences",
    response_model=UserInfoResponse,
    summary="修改模型与智能体偏好",
    description="快捷调整用户默认选用的 LLM 模型与智能体策略偏好",
)
async def update_user_preferences(
    request: UpdatePreferenceRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserInfoResponse:
    """快捷更新默认模型与默认 Agent."""
    repo = UserRepository(db)

    update_fields = request.model_dump(exclude_unset=True)
    updated_user = await repo.update(current_user.id, **update_fields)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    logger.info(
        f"Updated LLM preferences for user={current_user.username}: {update_fields}"
    )

    return UserInfoResponse(
        code=0,
        message="success",
        data=UserInfoData(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            avatar_url=updated_user.avatar_url,
            preferences=updated_user.preferences or {},
            default_model=updated_user.default_model,
            default_agent=updated_user.default_agent,
            created_at=updated_user.created_at,
        ),
    )


@router.get(
    "/stats",
    response_model=UsageStatsResponse,
    summary="获取用量统计",
    description="聚合计算当前用户的累计对话数、消息数、Token 消耗及今日用量",
)
async def get_user_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UsageStatsResponse:
    """计算用户的用量统计."""
    user_id = current_user.id
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. 累计会话数
    conv_stmt = (
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.user_id == user_id)
    )
    total_convs = (await db.execute(conv_stmt)).scalar_one() or 0

    # 2. 累计消息数与累计 Tokens (仅统计有效未软删除的消息)
    all_msg_stmt = select(
        func.count(Message.id),
        func.coalesce(func.sum(Message.tokens_used), 0),
    ).where(
        Message.user_id == user_id,
        Message.is_deleted == False,  # noqa: E712
    )
    all_msg_res = await db.execute(all_msg_stmt)
    total_msgs, total_tokens = all_msg_res.one()

    # 3. 今日新增消息数与今日 Tokens
    today_stmt = select(
        func.count(Message.id),
        func.coalesce(func.sum(Message.tokens_used), 0),
    ).where(
        Message.user_id == user_id,
        Message.is_deleted == False,  # noqa: E712
        Message.created_at >= today_start,
    )
    today_res = await db.execute(today_stmt)
    today_msgs, today_tokens = today_res.one()

    return UsageStatsResponse(
        code=0,
        message="success",
        data=UsageStatsData(
            total_messages=int(total_msgs or 0),
            total_tokens=int(total_tokens or 0),
            total_conversations=int(total_convs or 0),
            today_messages=int(today_msgs or 0),
            today_tokens=int(today_tokens or 0),
        ),
    )
