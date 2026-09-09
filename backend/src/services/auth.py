"""认证依赖注入模块.

提供 FastAPI 依赖注入函数，用于获取当前认证用户.
支持认证开关，便于 Cloudflare 同域部署时绕过认证.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.configs.config import Settings, get_settings
from src.engine.mysql_client import get_db_session
from src.models.user import User, UserRepository
from src.utils.jwt import get_jwt_manager


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> User:
    """获取当前认证用户 (依赖注入).

    根据配置自动选择认证模式:
    - auth_enabled=False: 返回匿名用户 (用于开发/测试)
    - auth_mode=forward-auth: 从 Kong oauth2-forward-auth 注入的 X-Auth-Request-* Header 解析并自动落库
    - auth_mode=cloudflare: 从 CF-Access-Jwt-Assertion Header 解析
    - auth_mode=logto: 从 Authorization Bearer Token 解析

    Args:
        request: FastAPI Request 对象
        settings: 应用配置
        db: 数据库异步会话 (可选注入)

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
            created_at=datetime.now(UTC),
        )

    # Kong Forward-Auth 网关鉴权模式 (生产推荐)
    if settings.auth_mode == "forward-auth":
        return await _get_user_from_forward_auth(request, settings, db)

    # Cloudflare Access 同域认证模式
    if settings.auth_mode == "cloudflare":
        return await _get_user_from_cloudflare(request, settings)

    # Logto / JWT Bearer Token 认证模式
    return await _get_user_from_jwt(request, settings)


async def _get_user_from_forward_auth(
    request: Request,
    settings: Settings,
    db: AsyncSession | None = None,
) -> User:
    """从 Kong Forward-Auth 注入的请求头中解析用户.

    Kong Lua 插件 oauth2-forward-auth 在校验通过后会注入:
    - X-Auth-Request-User: Logto sub / 用户唯一身份锚点
    - X-Auth-Request-Preferred-Username: GitHub 登录用户名
    - X-Auth-Request-Email: 用户邮箱

    Args:
        request: FastAPI Request 对象
        settings: 应用配置
        db: 数据库异步会话 (用于自动落库或查询)

    Returns:
        User: 用户对象

    Raises:
        HTTPException: 缺少网关注入身份头时抛出 401
    """
    sso_id = request.headers.get("X-Auth-Request-User") or request.headers.get(
        "x-auth-request-user"
    )
    if not sso_id:
        logger.warning("Missing X-Auth-Request-User header in forward-auth mode")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing SSO identity headers (X-Auth-Request-User)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = (
        request.headers.get("X-Auth-Request-Preferred-Username")
        or request.headers.get("x-auth-request-preferred-username")
        or sso_id
    )
    email = request.headers.get("X-Auth-Request-Email") or request.headers.get(
        "x-auth-request-email"
    )
    # 若网关将 sub 填入 email 且不含 @，清除脏 email
    if email and "@" not in email:
        email = None

    avatar_url = (
        f"https://github.com/{username}.png"
        if username and username != sso_id
        else None
    )

    # 尝试通过 OAuth2-Proxy / Logto 传递的 Access Token 解析真实的 GitHub 用户名和官方头像
    access_token = request.headers.get(
        "X-Auth-Request-Access-Token"
    ) or request.headers.get("x-auth-request-access-token")

    if access_token and (username == sso_id or not avatar_url):
        try:
            from src.services.logto_service import get_logto_service

            logto_service = get_logto_service()
            user_info = await logto_service.get_user_info(access_token)
            if user_info:
                identities = user_info.get("identities", {})
                github_details = identities.get("github", {}).get("details", {})
                real_username = (
                    github_details.get("login")
                    or github_details.get("username")
                    or user_info.get("username")
                    or user_info.get("name")
                    or user_info.get("preferred_username")
                )
                if real_username:
                    username = real_username

                real_avatar = (
                    github_details.get("avatar_url")
                    or user_info.get("picture")
                    or (
                        f"https://github.com/{username}.png"
                        if username and username != sso_id
                        else None
                    )
                )
                if real_avatar:
                    avatar_url = real_avatar

                real_email = user_info.get("email")
                if real_email and "@" in real_email:
                    email = real_email
        except Exception as e:
            logger.warning(f"Failed to fetch profile from Logto: {e}")

    # 若注入了数据库异步会话，自动完成持久化同步并返回数据库 User 实体
    if db is not None:
        user_repo = UserRepository(db)
        user = await user_repo.get_or_create_by_sso(
            sso_id=sso_id,
            username=username,
            email=email,
            avatar_url=avatar_url,
        )
        return user

    # 无 DB 会话环境 (如独立轻量单元测试) 兜底构造 User 对象
    return User(
        id=sso_id,
        username=username,
        email=email,
        avatar_url=avatar_url,
        preferences={},
        default_model=settings.default_model,
        default_agent="auto",
        logto_id=sso_id,
        created_at=datetime.now(UTC),
    )


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
        created_at=datetime.now(UTC),
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
            created_at=datetime.now(UTC),
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
    db: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> User | None:
    """获取可选当前用户 (依赖注入).

    认证失败时返回 None 而非抛出异常，适用于公开接口.

    Args:
        request: FastAPI Request 对象
        settings: 应用配置
        db: 数据库异步会话 (可选注入)

    Returns:
        User | None: 用户对象或 None
    """
    try:
        return await get_current_user(request, settings, db)
    except HTTPException:
        return None
