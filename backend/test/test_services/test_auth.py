"""认证依赖注入模块测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from src.services.auth import (
    _get_user_from_cloudflare,
    _get_user_from_jwt,
    get_current_active_user,
    get_current_user,
    get_optional_user,
)


class TestGetCurrentUser:
    """get_current_user 依赖注入测试类."""

    @pytest.mark.asyncio
    async def test_auth_disabled(self):
        """测试认证关闭 - 返回匿名用户."""
        mock_request = MagicMock(spec=Request)
        mock_settings = MagicMock()
        mock_settings.auth_enabled = False
        mock_settings.default_model = "deepseek-v4-flash"

        user = await get_current_user(mock_request, mock_settings)

        assert user.id == "anonymous"
        assert user.username == "anonymous"
        assert user.default_model == "deepseek-v4-flash"

    @pytest.mark.asyncio
    async def test_auth_mode_cloudflare(self):
        """测试 Cloudflare 认证模式."""
        mock_request = MagicMock(spec=Request)
        mock_settings = MagicMock()
        mock_settings.auth_enabled = True
        mock_settings.auth_mode = "cloudflare"

        with patch(
            "src.services.auth._get_user_from_cloudflare", new_callable=AsyncMock
        ) as mock_cf:
            mock_cf.return_value = MagicMock()
            user = await get_current_user(mock_request, mock_settings)
            assert user is not None
            mock_cf.assert_called_once_with(mock_request, mock_settings)

    @pytest.mark.asyncio
    async def test_auth_mode_logto(self):
        """测试 Logto 认证模式."""
        mock_request = MagicMock(spec=Request)
        mock_settings = MagicMock()
        mock_settings.auth_enabled = True
        mock_settings.auth_mode = "logto"

        with patch(
            "src.services.auth._get_user_from_jwt", new_callable=AsyncMock
        ) as mock_jwt:
            mock_jwt.return_value = MagicMock()
            user = await get_current_user(mock_request, mock_settings)
            assert user is not None
            mock_jwt.assert_called_once_with(mock_request, mock_settings)


class TestGetUserFromJWT:
    """_get_user_from_jwt 测试类."""

    @pytest.mark.asyncio
    async def test_missing_authorization_header(self):
        """测试缺少 Authorization Header."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_settings = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await _get_user_from_jwt(mock_request, mock_settings)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_authorization_format(self):
        """测试 Authorization 格式错误."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "InvalidFormat token"
        mock_settings = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await _get_user_from_jwt(mock_request, mock_settings)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """测试无效 Token."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Bearer invalid-token"
        mock_settings = MagicMock()

        with patch("src.services.auth.get_jwt_manager") as mock_get_jwt:
            mock_jwt = MagicMock()
            mock_jwt.verify_token.return_value = None
            mock_get_jwt.return_value = mock_jwt

            with pytest.raises(HTTPException) as exc_info:
                await _get_user_from_jwt(mock_request, mock_settings)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token(self):
        """测试有效 Token."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid-token"
        mock_settings = MagicMock()
        mock_settings.default_model = "deepseek-v4-flash"

        with patch("src.services.auth.get_jwt_manager") as mock_get_jwt:
            mock_jwt = MagicMock()
            mock_jwt.verify_token.return_value = {
                "sub": "user-123",
                "username": "testuser",
                "email": "test@example.com",
                "avatar_url": "https://example.com/avatar.png",
                "preferences": {"theme": "dark"},
                "default_model": "deepseek-v4-flash",
                "default_agent": "auto",
                "logto_id": "logto-123",
            }
            mock_get_jwt.return_value = mock_jwt

            user = await _get_user_from_jwt(mock_request, mock_settings)

            assert user.id == "user-123"
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.preferences == {"theme": "dark"}


class TestGetUserFromCloudflare:
    """_get_user_from_cloudflare 测试类."""

    @pytest.mark.asyncio
    async def test_missing_cf_jwt(self):
        """测试缺少 Cloudflare JWT."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_settings = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await _get_user_from_cloudflare(mock_request, mock_settings)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_cf_jwt_format(self):
        """测试 Cloudflare JWT 格式错误."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "invalid-jwt"
        mock_settings = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await _get_user_from_cloudflare(mock_request, mock_settings)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_cf_jwt(self):
        """测试有效 Cloudflare JWT."""
        import base64
        import json

        payload = {
            "sub": "cf-user-123",
            "email": "test@example.com",
        }
        payload_b64 = (
            base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        )
        mock_jwt = f"header.{payload_b64}.signature"

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = mock_jwt
        mock_settings = MagicMock()
        mock_settings.default_model = "deepseek-v4-flash"

        user = await _get_user_from_cloudflare(mock_request, mock_settings)

        assert user.id == "cf-user-123"
        assert user.username == "test"
        assert user.email == "test@example.com"


class TestGetCurrentActiveUser:
    """get_current_active_user 测试类."""

    @pytest.mark.asyncio
    async def test_get_current_active_user(self):
        """测试获取当前活跃用户."""
        mock_user = MagicMock()
        result = await get_current_active_user(mock_user)
        assert result is mock_user


class TestGetOptionalUser:
    """get_optional_user 测试类."""

    @pytest.mark.asyncio
    async def test_get_optional_user_success(self):
        """测试获取可选用户 - 成功."""
        mock_request = MagicMock(spec=Request)
        mock_settings = MagicMock()

        with patch(
            "src.services.auth.get_current_user", new_callable=AsyncMock
        ) as mock_get_user:
            mock_user = MagicMock()
            mock_get_user.return_value = mock_user
            result = await get_optional_user(mock_request, mock_settings)
            assert result is mock_user

    @pytest.mark.asyncio
    async def test_get_optional_user_failure(self):
        """测试获取可选用户 - 失败返回 None."""
        mock_request = MagicMock(spec=Request)
        mock_settings = MagicMock()

        with patch(
            "src.services.auth.get_current_user", new_callable=AsyncMock
        ) as mock_get_user:
            mock_get_user.side_effect = HTTPException(status_code=401)
            result = await get_optional_user(mock_request, mock_settings)
            assert result is None
