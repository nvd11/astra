"""认证依赖注入模块.

提供 FastAPI 依赖注入函数，用于获取当前认证用户.
支持认证开关，便于 Cloudflare 同域部署时绕过认证.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from loguru import logger

from src.configs.config import Settings, get_settings
from src.models.user import User
from src.utils.jwt import get_jwt_manager


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """获取当前认证用户 (依赖注入).

    根据配置自动选择认证模式:
    - auth_enabled=False: 返回匿名用户 (用于开发/测试)
    - auth_mode=cloudflare: 从 CF-Access-Jwt-Assertion Header 解析
    - auth_mode=logto: 从 Authorization Bearer Token 解析

    Args:
        request: FastAPI Request 对象
        settings: 应用配置

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 认证失败时抛出 401
    """
    # 认证完全关闭 (开发/测试模式)
    if not settings.auth_enabled:
        logger.debug("Auth disabled, returning anonymous user")
        return User(
            id="anonymous",
            username="anonymous",
            email=None,
            avatar_url=None,
            preferences={},
            default_model=settings.default_model,
            default_agent="auto",
            logto_id=None,
        )

    # Cloudflare Access 同域认证模式
    if settings.auth_mode == "cloudflare":
        return await _get_user_from_cloudflare(request, settings)

    # Logto / JWT Bearer Token 认证模式
    return await _get_user_from_jwt(request, settings)


async def _get_user_from_jwt(request: Request, settings: Settings) -> User:
    """从 JWT Bearer Token 解析用户.

    Args:
        request: FastAPI Request 对象
        settings: 应用配置

    Returns:
        User: 用户对象

    Raises:
        HTTPException: 认证失败
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.replace("Bearer ", "")
    jwt_manager = get_jwt_manager()
    payload = jwt_manager.verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从数据库加载用户 (这里先返回基础信息，后续可集成 UserRepository)
    user_id = payload.get("sub", "")
    username = payload.get("username", "")

    return User(
        id=user_id,
        username=username,
        email=payload.get("email"),
        avatar_url=payload.get("avatar_url"),
        preferences=payload.get("preferences", {}),
        default_model=payload.get("default_model", settings.default_model),
        default_agent=payload.get("default_agent", "auto"),
        logto_id=payload.get("logto_id"),
    )


async def _get_user_from_cloudflare(request: Request, settings: Settings) -> User:
    """从 Cloudflare Access JWT 解析用户.

    Cloudflare Access 会在同域部署时自动注入 CF-Access-Jwt-Assertion Header.

    Args:
        request: FastAPI Request 对象
        settings: 应用配置

    Returns:
        User: 用户对象

    Raises:
        HTTPException: 认证失败
    """
    cf_jwt = request.headers.get("CF-Access-Jwt-Assertion")
    if not cf_jwt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Cloudflare Access JWT",
        )

    # TODO: 验证 Cloudflare JWT (使用 cloudflare_team_name 和 cloudflare_audience)
    # 这里简化处理，实际应使用 PyJWT 验证 CF 的公钥
    logger.warning("Cloudflare Access JWT validation not fully implemented")

    # 从 CF JWT 中提取用户信息 (简化版)
    try:
        import base64
        import json

        # 解析 JWT payload (不验证签名，仅用于开发)
        parts = cf_jwt.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        payload_b64 = parts[1]
        # 补齐 base64 padding
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        email = payload.get("email", "")
        username = email.split("@")[0] if email else "cloudflare-user"

        return User(
            id=payload.get("sub", ""),
            username=username,
            email=email,
            avatar_url=None,
            preferences={},
            default_model=settings.default_model,
            default_agent="auto",
            logto_id=None,
        )
    except Exception as e:
        logger.error(f"Failed to parse Cloudflare JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Cloudflare Access JWT",
        ) from e


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """获取当前活跃用户 (依赖注入).

    Args:
        current_user: 当前用户

    Returns:
        User: 当前用户对象
    """
    # 可在此添加用户状态检查 (如是否被禁用)
    return current_user


async def get_optional_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> User | None:
    """获取可选当前用户 (依赖注入).

    认证失败时返回 None 而非抛出异常，适用于公开接口.

    Args:
        request: FastAPI Request 对象
        settings: 应用配置

    Returns:
        User | None: 用户对象或 None
    """
    try:
        return await get_current_user(request, settings)
    except HTTPException:
        return None
