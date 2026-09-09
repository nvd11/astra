"""认证路由模块.

提供登录、回调、刷新令牌、登出等认证相关端点.
支持认证开关，便于 Cloudflare 同域部署.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.configs.config import Settings, get_settings
from src.engine.mysql_client import get_db_session
from src.middleware.rate_limit import extract_client_ip
from src.models.requests import LoginRequest, LogtoCallbackRequest, RefreshTokenRequest
from src.models.responses import (
    BaseResponse,
    TokenResponse,
    TokenResponseData,
    UserInfoData,
    UserInfoResponse,
)
from src.models.user import SessionRepository, User, UserRepository
from src.services.auth import get_current_user
from src.services.logto_service import get_logto_service
from src.utils.jwt import get_jwt_manager

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="账密登录",
    description="基础用户名密码登录 (仅用于开发/测试，生产环境应使用 Logto SSO)",
)
async def login(
    request: LoginRequest,
    raw_request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """账密登录端点.

    Args:
        request: 登录请求
        raw_request: 原生 HTTP 请求 (提取 IP 与 UA)
        settings: 应用配置
        db: 数据库会话

    Returns:
        TokenResponse: 令牌响应

    Raises:
        HTTPException: 认证失败
    """
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Authentication is disabled"
        )

    if settings.auth_mode not in ("logto", "forward-auth"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Login endpoint is not available in {settings.auth_mode} mode",
        )

    # TODO: 实现真实的密码验证 (当前为简化版)
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(request.username)

    if not user:
        # 开发模式下自动创建用户
        user = await user_repo.create(
            username=request.username,
            email=f"{request.username}@example.com",
        )
        logger.info(f"Auto-created user: {user.username}")

    # 签发令牌
    jwt_manager = get_jwt_manager()
    access_token = jwt_manager.create_access_token(user.id, user.username)
    refresh_token = jwt_manager.create_refresh_token(user.id, user.username)

    # 保存会话 (捕获真实客户端 IP 与 UA 设备信息)
    client_ip = extract_client_ip(raw_request)
    device_info = raw_request.headers.get("User-Agent") or "Web Browser"

    session_repo = SessionRepository(db)
    expires_at = datetime.now(UTC) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    await session_repo.create(
        user_id=user.id,
        refresh_token=refresh_token,
        device_info=device_info[:255],
        ip_address=client_ip,
        expires_at=expires_at,
    )

    return TokenResponse(
        data=TokenResponseData(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=UserInfoData(
                id=user.id,
                username=user.username,
                email=user.email,
                avatar_url=user.avatar_url,
                preferences=user.preferences,
                default_model=user.default_model,
                default_agent=user.default_agent,
                created_at=user.created_at,
            ),
        )
    )


@router.get(
    "/logto/authorize",
    response_model=BaseResponse[dict[str, Any]],
    summary="获取 Logto 授权 URL",
    description="生成 Logto SSO 授权跳转链接",
)
async def logto_authorize(
    settings: Annotated[Settings, Depends(get_settings)],
) -> BaseResponse[dict[str, Any]]:
    """获取 Logto 授权 URL.

    Args:
        settings: 应用配置

    Returns:
        BaseResponse[dict[str, Any]]: 包含授权 URL 的响应
    """
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Authentication is disabled"
        )

    if settings.auth_mode != "logto":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Login endpoint is not available in {settings.auth_mode} mode",
        )

    logto_service = get_logto_service()
    state = str(uuid.uuid4())
    auth_url = logto_service.get_authorization_url(state)

    return BaseResponse(data={"authorization_url": auth_url, "state": state})


@router.post(
    "/logto/callback",
    response_model=TokenResponse,
    summary="Logto SSO 回调",
    description="处理 Logto 授权码回调并签发系统令牌",
)
async def logto_callback(
    request: LogtoCallbackRequest,
    raw_request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """Logto SSO 回调端点.

    Args:
        request: 回调请求
        raw_request: 原生 HTTP 请求 (提取 IP 与 UA)
        settings: 应用配置
        db: 数据库会话

    Returns:
        TokenResponse: 令牌响应

    Raises:
        HTTPException: 认证失败
    """
    if not settings.auth_enabled or settings.auth_mode != "logto":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Logto SSO is not enabled"
        )

    logto_service = get_logto_service()
    user_info = await logto_service.validate_callback(request.code, request.state)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to validate Logto callback",
        )

    # 获取或创建用户
    user_repo = UserRepository(db)
    user = await user_repo.get_or_create_by_logto(
        logto_id=user_info["logto_id"],
        username=user_info["username"],
        email=user_info.get("email"),
        avatar_url=user_info.get("avatar_url"),
    )

    # 签发令牌
    jwt_manager = get_jwt_manager()
    access_token = jwt_manager.create_access_token(user.id, user.username)
    refresh_token = jwt_manager.create_refresh_token(user.id, user.username)

    # 保存会话 (捕获真实客户端 IP 与 UA 设备信息)
    client_ip = extract_client_ip(raw_request)
    device_info = raw_request.headers.get("User-Agent") or "Web Browser"

    session_repo = SessionRepository(db)
    expires_at = datetime.now(UTC) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    await session_repo.create(
        user_id=user.id,
        refresh_token=refresh_token,
        device_info=device_info[:255],
        ip_address=client_ip,
        expires_at=expires_at,
    )

    return TokenResponse(
        data=TokenResponseData(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=UserInfoData(
                id=user.id,
                username=user.username,
                email=user.email,
                avatar_url=user.avatar_url,
                preferences=user.preferences,
                default_model=user.default_model,
                default_agent=user.default_agent,
                created_at=user.created_at,
            ),
        )
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新令牌",
    description="使用 Refresh Token 获取新的 Access Token",
)
async def refresh_token(
    request: RefreshTokenRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """刷新令牌端点.

    Args:
        request: 刷新请求
        settings: 应用配置
        db: 数据库会话

    Returns:
        TokenResponse: 新的令牌响应

    Raises:
        HTTPException: 刷新失败
    """
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Authentication is disabled"
        )

    jwt_manager = get_jwt_manager()
    result = jwt_manager.refresh_access_token(request.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # 验证会话是否存在
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_refresh_token(request.refresh_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found"
        )

    # 更新会话最后活跃时间
    session.last_active_at = datetime.now(UTC)
    await db.flush()

    # 获取用户信息
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(session.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return TokenResponse(
        data=TokenResponseData(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user=UserInfoData(
                id=user.id,
                username=user.username,
                email=user.email,
                avatar_url=user.avatar_url,
                preferences=user.preferences,
                default_model=user.default_model,
                default_agent=user.default_agent,
                created_at=user.created_at,
            ),
        )
    )


@router.post(
    "/logout",
    response_model=BaseResponse[dict[str, Any]],
    summary="登出",
    description="登出并删除当前会话 (支持 Forward-Auth 清理与 Token 删除)",
)
async def logout(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    request: RefreshTokenRequest | None = None,
) -> BaseResponse[dict[str, Any]]:
    """登出端点.

    Args:
        settings: 应用配置
        db: 数据库会话
        request: 可选的包含 Refresh Token 的请求

    Returns:
        BaseResponse[dict[str, Any]]: 登出结果
    """
    if not settings.auth_enabled:
        return BaseResponse(data={"message": "Auth disabled, no session to logout"})

    deleted = False
    if request and request.refresh_token:
        session_repo = SessionRepository(db)
        deleted = await session_repo.delete_by_refresh_token(request.refresh_token)

    return BaseResponse(
        data={
            "message": "Logged out successfully",
            "deleted": deleted,
            "signout_url": "/oauth2/sign_out?rd=/astra/",
        }
    )


@router.get(
    "/me",
    response_model=UserInfoResponse,
    summary="获取当前用户信息",
    description="获取当前认证用户的详细资料",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserInfoResponse:
    """获取当前用户信息端点.

    Args:
        current_user: 当前用户 (依赖注入)

    Returns:
        UserInfoResponse: 用户信息
    """
    return UserInfoResponse(
        code=0,
        message="success",
        data=UserInfoData(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            avatar_url=current_user.avatar_url,
            preferences=current_user.preferences,
            default_model=current_user.default_model,
            default_agent=current_user.default_agent,
            created_at=current_user.created_at or datetime.now(UTC),
        ),
    )
