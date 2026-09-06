"""JWT 工具模块.

提供 Access Token / Refresh Token 的签发、验证与刷新功能.
支持认证开关，便于 Cloudflare 同域部署时绕过 JWT 校验.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from loguru import logger

from src.configs.config import get_settings


class JWTManager:
    """JWT 令牌管理器."""

    def __init__(self) -> None:
        """初始化 JWT 管理器."""
        self.settings = get_settings()
        self.secret = self.settings.jwt_secret
        self.algorithm = self.settings.jwt_algorithm
        self.access_expire_minutes = self.settings.jwt_access_token_expire_minutes
        self.refresh_expire_days = self.settings.jwt_refresh_token_expire_days

    def create_access_token(
        self,
        user_id: str,
        username: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """签发 Access Token.

        Args:
            user_id: 用户唯一 ID
            username: 用户名
            extra_claims: 额外自定义 claims

        Returns:
            str: JWT Access Token
        """
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=self.access_expire_minutes)

        payload: dict[str, Any] = {
            "sub": user_id,
            "username": username,
            "iat": now,
            "exp": expire,
            "type": "access",
            "jti": str(uuid.uuid4()),
        }
        if extra_claims:
            payload.update(extra_claims)

        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        logger.debug(f"Created access token for user={username}, expires={expire}")
        return token

    def create_refresh_token(
        self,
        user_id: str,
        username: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """签发 Refresh Token.

        Args:
            user_id: 用户唯一 ID
            username: 用户名
            extra_claims: 额外自定义 claims

        Returns:
            str: JWT Refresh Token
        """
        now = datetime.now(UTC)
        expire = now + timedelta(days=self.refresh_expire_days)

        payload: dict[str, Any] = {
            "sub": user_id,
            "username": username,
            "iat": now,
            "exp": expire,
            "type": "refresh",
            "jti": str(uuid.uuid4()),
        }
        if extra_claims:
            payload.update(extra_claims)

        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        logger.debug(f"Created refresh token for user={username}, expires={expire}")
        return token

    def verify_token(
        self, token: str, token_type: str = "access"
    ) -> dict[str, Any] | None:
        """验证 JWT Token.

        Args:
            token: JWT Token 字符串
            token_type: 期望的 token 类型 (access/refresh)

        Returns:
            dict | None: 验证成功返回 payload，失败返回 None
        """
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                logger.warning(
                    f"Token type mismatch: expected={token_type}, got={payload.get('type')}"
                )
                return None
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any] | None:
        """使用 Refresh Token 刷新 Access Token.

        Args:
            refresh_token: Refresh Token 字符串

        Returns:
            dict | None: 包含新 access_token 和 refresh_token 的字典，失败返回 None
        """
        payload = self.verify_token(refresh_token, token_type="refresh")
        if payload is None:
            return None

        user_id = payload["sub"]
        username = payload["username"]

        new_access_token = self.create_access_token(user_id, username)
        new_refresh_token = self.create_refresh_token(user_id, username)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": self.access_expire_minutes * 60,
        }

    def extract_user_id(self, token: str) -> str | None:
        """从 Token 中提取用户 ID.

        Args:
            token: JWT Token 字符串

        Returns:
            str | None: 用户 ID，失败返回 None
        """
        payload = self.verify_token(token)
        return payload.get("sub") if payload else None


# 全局单例
_jwt_manager: JWTManager | None = None


def get_jwt_manager() -> JWTManager:
    """获取 JWT 管理器单例.

    Returns:
        JWTManager: JWT 管理器实例
    """
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager
