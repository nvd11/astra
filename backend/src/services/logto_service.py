"""Logto SSO 服务模块.

提供 Logto 统一认证集成，支持授权码交换、用户信息获取.
支持认证开关，便于 Cloudflare 同域部署时禁用 Logto.
"""

from typing import Any, cast

import httpx
from loguru import logger

from src.configs.config import get_settings


class LogtoService:
    """Logto SSO 认证服务."""

    def __init__(self) -> None:
        """初始化 Logto 服务."""
        self.settings = get_settings()
        self.endpoint = self.settings.logto_endpoint.rstrip("/")
        self.app_id = self.settings.logto_app_id
        self.app_secret = self.settings.logto_app_secret
        self.redirect_uri = self.settings.logto_redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """生成 Logto 授权跳转 URL.

        Args:
            state: 状态参数 (防 CSRF)

        Returns:
            str: 授权 URL
        """
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid profile email",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.endpoint}/oidc/auth?{query}"
        logger.debug(f"Generated Logto authorization URL: {url}")
        return url

    async def exchange_code_for_token(self, code: str) -> dict[str, Any] | None:
        """使用授权码交换 Access Token.

        Args:
            code: 授权码

        Returns:
            dict | None: Token 响应，失败返回 None
        """
        token_url = f"{self.endpoint}/oidc/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data, timeout=10.0)
                response.raise_for_status()
                token_data = cast(dict[str, Any], response.json())
                logger.info("Successfully exchanged code for token")
                return token_data
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            return None

    async def get_user_info(self, access_token: str) -> dict[str, Any] | None:
        """获取 Logto 用户信息.

        Args:
            access_token: Logto Access Token

        Returns:
            dict | None: 用户信息，失败返回 None
        """
        userinfo_url = f"{self.endpoint}/oidc/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(userinfo_url, headers=headers, timeout=10.0)
                response.raise_for_status()
                user_info = cast(dict[str, Any], response.json())
                logger.info(f"Retrieved user info: sub={user_info.get('sub')}")
                return user_info
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def validate_callback(self, code: str, state: str) -> dict[str, Any] | None:
        """验证 Logto 回调并返回用户信息.

        Args:
            code: 授权码
            state: 状态参数

        Returns:
            dict | None: 包含用户信息的字典，失败返回 None
        """
        # 交换 token
        token_data = await self.exchange_code_for_token(code)
        if not token_data:
            return None

        access_token = token_data.get("access_token")
        if not access_token:
            logger.error("No access_token in token response")
            return None

        # 获取用户信息
        user_info = await self.get_user_info(access_token)
        if not user_info:
            return None

        return {
            "logto_id": user_info.get("sub"),
            "username": user_info.get("username") or user_info.get("name"),
            "email": user_info.get("email"),
            "avatar_url": user_info.get("picture"),
            "raw_user_info": user_info,
        }


# 全局单例
_logto_service: LogtoService | None = None


def get_logto_service() -> LogtoService:
    """获取 Logto 服务单例.

    Returns:
        LogtoService: Logto 服务实例
    """
    global _logto_service
    if _logto_service is None:
        _logto_service = LogtoService()
    return _logto_service
