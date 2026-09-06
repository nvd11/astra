"""JWT 工具模块测试."""

import os
from unittest.mock import patch

import pytest

from src.utils.jwt import JWTManager, get_jwt_manager


class TestJWTManager:
    """JWT 管理器测试类."""

    @pytest.fixture
    def jwt_manager(self):
        """创建 JWT 管理器实例."""
        with patch.dict(
            os.environ,
            {
                "APP_JWT_SECRET": "test-secret-key",
                "APP_JWT_ALGORITHM": "HS256",
                "APP_JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
                "APP_JWT_REFRESH_TOKEN_EXPIRE_DAYS": "1",
            },
        ):
            from src.configs.config import get_settings

            get_settings.cache_clear()
            yield JWTManager()
            get_settings.cache_clear()

    def test_init(self, jwt_manager):
        """测试初始化."""
        assert jwt_manager.secret == "test-secret-key"
        assert jwt_manager.algorithm == "HS256"
        assert jwt_manager.access_expire_minutes == 30
        assert jwt_manager.refresh_expire_days == 1

    def test_create_access_token(self, jwt_manager):
        """测试创建 Access Token."""
        token = jwt_manager.create_access_token("user-123", "testuser")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, jwt_manager):
        """测试创建 Refresh Token."""
        token = jwt_manager.create_refresh_token("user-123", "testuser")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_success(self, jwt_manager):
        """测试验证 Token - 成功."""
        token = jwt_manager.create_access_token("user-123", "testuser")
        payload = jwt_manager.verify_token(token, token_type="access")

        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"

    def test_verify_token_wrong_type(self, jwt_manager):
        """测试验证 Token - 类型不匹配."""
        token = jwt_manager.create_access_token("user-123", "testuser")
        payload = jwt_manager.verify_token(token, token_type="refresh")

        assert payload is None

    def test_verify_token_invalid(self, jwt_manager):
        """测试验证 Token - 无效 Token."""
        payload = jwt_manager.verify_token("invalid-token")
        assert payload is None

    def test_refresh_access_token(self, jwt_manager):
        """测试刷新 Access Token."""
        refresh_token = jwt_manager.create_refresh_token("user-123", "testuser")
        result = jwt_manager.refresh_access_token(refresh_token)

        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 30 * 60

    def test_refresh_access_token_invalid(self, jwt_manager):
        """测试刷新 Access Token - 无效 Refresh Token."""
        result = jwt_manager.refresh_access_token("invalid-token")
        assert result is None

    def test_extract_user_id(self, jwt_manager):
        """测试提取用户 ID."""
        token = jwt_manager.create_access_token("user-123", "testuser")
        user_id = jwt_manager.extract_user_id(token)
        assert user_id == "user-123"

    def test_extract_user_id_invalid(self, jwt_manager):
        """测试提取用户 ID - 无效 Token."""
        user_id = jwt_manager.extract_user_id("invalid-token")
        assert user_id is None


class TestGetJWTManager:
    """get_jwt_manager 单例测试类."""

    def test_get_jwt_manager_singleton(self):
        """测试单例模式."""
        manager1 = get_jwt_manager()
        manager2 = get_jwt_manager()
        assert manager1 is manager2
