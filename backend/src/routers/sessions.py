"""会话管理路由模块.

提供用户设备会话的查询与删除功能.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.configs.config import Settings, get_settings
from src.engine.mysql_client import get_db_session
from src.models.responses import BaseResponse, SessionListResponse, UserSessionItem
from src.models.user import SessionRepository, User
from src.services.auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get(
    "",
    response_model=SessionListResponse,
    summary="获取当前用户所有会话",
    description="查询当前登录用户的所有活跃设备会话",
)
async def list_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SessionListResponse:
    """获取当前用户所有会话.

    Args:
        current_user: 当前用户
        settings: 应用配置
        db: 数据库会话

    Returns:
        SessionListResponse: 会话列表
    """
    if not settings.auth_enabled:
        return SessionListResponse(data=[])

    session_repo = SessionRepository(db)
    sessions = await session_repo.get_by_user_id(current_user.id)

    items = [
        UserSessionItem(
            id=session.id,
            device_info=session.device_info,
            ip_address=session.ip_address,
            last_active_at=session.last_active_at,
            expires_at=session.expires_at,
            is_current=False,  # TODO: 从请求中识别当前会话
        )
        for session in sessions
    ]

    return SessionListResponse(data=items)


@router.delete(
    "/{session_id}",
    response_model=BaseResponse[dict[str, Any]],
    summary="删除指定会话",
    description="删除当前用户的指定设备会话 (踢出设备)",
)
async def delete_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[dict[str, Any]]:
    """删除指定会话.

    Args:
        session_id: 会话 ID
        current_user: 当前用户
        settings: 应用配置
        db: 数据库会话

    Returns:
        BaseResponse[dict]: 删除结果

    Raises:
        HTTPException: 会话不存在或无权限
    """
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Authentication is disabled"
        )

    try:
        session_repo = SessionRepository(db)
        sessions = await session_repo.get_by_user_id(current_user.id)

        target_session = next((s for s in sessions if s.id == session_id), None)
        if not target_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        await session_repo.delete_by_refresh_token(target_session.refresh_token)
        logger.info(f"Deleted session {session_id} for user {current_user.username}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error during session deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        ) from e

    return BaseResponse(data={"message": "Session deleted successfully"})


@router.delete(
    "",
    response_model=BaseResponse[dict[str, Any]],
    summary="删除所有会话 (除当前)",
    description="删除当前用户的所有其他设备会话",
)
async def delete_all_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    exclude_current: str | None = None,
) -> BaseResponse[dict[str, Any]]:
    """删除所有会话 (除当前).

    Args:
        current_user: 当前用户
        settings: 应用配置
        db: 数据库会话
        exclude_current: 要排除的 Refresh Token

    Returns:
        BaseResponse[dict]: 删除结果
    """
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Authentication is disabled"
        )

    try:
        session_repo = SessionRepository(db)
        count = await session_repo.delete_by_user_id(
            current_user.id, exclude_current=exclude_current
        )

        logger.info(f"Deleted {count} sessions for user {current_user.username}")
    except Exception as e:
        logger.error(f"Database error during sessions deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        ) from e

    return BaseResponse(data={"message": f"Deleted {count} sessions", "count": count})
