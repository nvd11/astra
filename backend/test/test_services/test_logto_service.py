"""Logto SSO 服务模块测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.logto_service import LogtoService, get_logto_service


class TestLogtoService:
    """Logto 服务测试类."""

    @pytest.fixture
    def logto_service(self):
        """创建 Logto 服务实例."""
        with patch("src.services.logto_service.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.logto_endpoint = "https://auth.test.local"
            mock_settings.logto_app_id = "test-app-id"
            mock_settings.logto_app_secret = "test-app-secret"
            mock_settings.logto_redirect_uri = "http://localhost:5173/callback"
            mock_get_settings.return_value = mock_settings
            yield LogtoService()

    def test_init(self, logto_service):
        """测试初始化."""
        assert logto_service.endpoint == "https://auth.test.local"
        assert logto_service.app_id == "test-app-id"
        assert logto_service.app_secret == "test-app-secret"
        assert logto_service.redirect_uri == "http://localhost:5173/callback"

    def test_get_authorization_url(self, logto_service):
        """测试生成授权 URL."""
        url = logto_service.get_authorization_url("test-state")
        assert "https://auth.test.local/oidc/auth" in url
        assert "client_id=test-app-id" in url
        assert "state=test-state" in url
        assert "response_type=code" in url

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, logto_service):
        """测试授权码交换 - 成功."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test-access-token"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await logto_service.exchange_code_for_token("test-code")

            assert result is not None
            assert result["access_token"] == "test-access-token"

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self, logto_service):
        """测试授权码交换 - 失败."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_context.post = AsyncMock(side_effect=Exception("Network error"))
            mock_client.return_value.__aenter__.return_value = mock_context
            result = await logto_service.exchange_code_for_token("test-code")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, logto_service):
        """测试获取用户信息 - 成功."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sub": "logto-user-123",
            "username": "testuser",
            "email": "test@example.com",
            "picture": "https://example.com/avatar.png",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await logto_service.get_user_info("test-access-token")

            assert result is not None
            assert result["sub"] == "logto-user-123"
            assert result["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_user_info_failure(self, logto_service):
        """测试获取用户信息 - 失败."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_context.get = AsyncMock(side_effect=Exception("Network error"))
            mock_client.return_value.__aenter__.return_value = mock_context
            result = await logto_service.get_user_info("test-access-token")

            assert result is None

    @pytest.mark.asyncio
    async def test_validate_callback_success(self, logto_service):
        """测试验证回调 - 成功."""
        with (
            patch.object(
                logto_service, "exchange_code_for_token", new_callable=AsyncMock
            ) as mock_exchange,
            patch.object(
                logto_service, "get_user_info", new_callable=AsyncMock
            ) as mock_get_user,
        ):

            mock_exchange.return_value = {"access_token": "test-access-token"}
            mock_get_user.return_value = {
                "sub": "logto-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "picture": "https://example.com/avatar.png",
            }

            result = await logto_service.validate_callback("test-code", "test-state")

            assert result is not None
            assert result["logto_id"] == "logto-user-123"
            assert result["username"] == "testuser"
            assert result["email"] == "test@example.com"
            assert result["avatar_url"] == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_validate_callback_exchange_failure(self, logto_service):
        """测试验证回调 - 交换失败."""
        with patch.object(
            logto_service, "exchange_code_for_token", new_callable=AsyncMock
        ) as mock_exchange:
            mock_exchange.return_value = None
            result = await logto_service.validate_callback("test-code", "test-state")
            assert result is None

    @pytest.mark.asyncio
    async def test_validate_callback_no_access_token(self, logto_service):
        """测试验证回调 - 无 Access Token."""
        with patch.object(
            logto_service, "exchange_code_for_token", new_callable=AsyncMock
        ) as mock_exchange:
            mock_exchange.return_value = {"id_token": "test-id-token"}
            result = await logto_service.validate_callback("test-code", "test-state")
            assert result is None

    @pytest.mark.asyncio
    async def test_validate_callback_user_info_failure(self, logto_service):
        """测试验证回调 - 获取用户信息失败."""
        with (
            patch.object(
                logto_service, "exchange_code_for_token", new_callable=AsyncMock
            ) as mock_exchange,
            patch.object(
                logto_service, "get_user_info", new_callable=AsyncMock
            ) as mock_get_user,
        ):

            mock_exchange.return_value = {"access_token": "test-access-token"}
            mock_get_user.return_value = None

            result = await logto_service.validate_callback("test-code", "test-state")
            assert result is None


class TestGetLogtoService:
    """get_logto_service 单例测试类."""

    def test_get_logto_service_singleton(self):
        """测试单例模式."""
        service1 = get_logto_service()
        service2 = get_logto_service()
        assert service1 is service2
