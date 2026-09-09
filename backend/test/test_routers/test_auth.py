"""认证路由测试."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.configs.config import Settings, get_settings
from src.models.user import User


class TestAuthRouter:
    """认证路由测试类."""

    def test_login_success(self, client: TestClient, app):
        """测试账密登录 - 成功."""
        with (
            patch("src.routers.auth.UserRepository") as mock_user_repo_class,
            patch("src.routers.auth.SessionRepository") as mock_session_repo_class,
            patch("src.routers.auth.get_jwt_manager") as mock_get_jwt,
        ):

            # Mock UserRepository
            mock_user_repo = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = "user-123"
            mock_user.username = "testuser"
            mock_user.email = "test@example.com"
            mock_user.avatar_url = None
            mock_user.preferences = {}
            mock_user.default_model = "deepseek-v4-flash"
            mock_user.default_agent = "auto"
            mock_user.created_at = datetime.datetime.now(datetime.UTC)
            mock_user_repo.get_by_username.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            # Mock SessionRepository
            mock_session_repo = AsyncMock()
            mock_session_repo_class.return_value = mock_session_repo

            # Mock JWT Manager
            mock_jwt = MagicMock()
            mock_jwt.create_access_token.return_value = "test-access-token"
            mock_jwt.create_refresh_token.return_value = "test-refresh-token"
            mock_get_jwt.return_value = mock_jwt

            response = client.post(
                "/auth/login",
                json={
                    "username": "testuser",
                    "password": "testpass123",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["access_token"] == "test-access-token"
            assert data["data"]["refresh_token"] == "test-refresh-token"
            assert data["data"]["user"]["username"] == "testuser"

    def test_login_auth_disabled(self, client: TestClient, app):
        """测试账密登录 - 认证关闭."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = False
        mock_settings.auth_mode = "logto"
        app.dependency_overrides[get_settings] = lambda: mock_settings

        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123",
            },
        )

        assert response.status_code == 403

    def test_logto_authorize_success(self, client: TestClient, app):
        """测试获取 Logto 授权 URL - 成功."""
        with patch("src.routers.auth.get_logto_service") as mock_get_logto:
            mock_settings = MagicMock(spec=Settings)
            mock_settings.auth_enabled = True
            mock_settings.auth_mode = "logto"
            app.dependency_overrides[get_settings] = lambda: mock_settings

            mock_logto = MagicMock()
            mock_logto.get_authorization_url.return_value = (
                "https://auth.test.local/oidc/auth?client_id=test"
            )
            mock_get_logto.return_value = mock_logto

            response = client.get("/auth/logto/authorize")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "authorization_url" in data["data"]
            assert "state" in data["data"]

    def test_logto_authorize_disabled(self, client: TestClient, app):
        """测试获取 Logto 授权 URL - 未启用 (认证关闭)."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = False
        mock_settings.auth_mode = "logto"
        app.dependency_overrides[get_settings] = lambda: mock_settings

        response = client.get("/auth/logto/authorize")
        assert response.status_code == 403

    def test_logto_authorize_wrong_mode(self, client: TestClient, app):
        """测试获取 Logto 授权 URL - 认证模式不匹配."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = True
        mock_settings.auth_mode = "cloudflare"
        app.dependency_overrides[get_settings] = lambda: mock_settings

        response = client.get("/auth/logto/authorize")
        assert response.status_code == 403

    def test_logto_callback_success(self, client: TestClient, app):
        """测试 Logto 回调 - 成功."""
        with (
            patch("src.routers.auth.get_logto_service") as mock_get_logto,
            patch("src.routers.auth.UserRepository") as mock_user_repo_class,
            patch("src.routers.auth.SessionRepository") as mock_session_repo_class,
            patch("src.routers.auth.get_jwt_manager") as mock_get_jwt,
        ):

            mock_settings = MagicMock(spec=Settings)
            mock_settings.auth_enabled = True
            mock_settings.auth_mode = "logto"
            mock_settings.jwt_access_token_expire_minutes = 120
            mock_settings.jwt_refresh_token_expire_days = 7
            app.dependency_overrides[get_settings] = lambda: mock_settings

            mock_logto = AsyncMock()
            mock_logto.validate_callback.return_value = {
                "logto_id": "logto-123",
                "username": "testuser",
                "email": "test@example.com",
                "avatar_url": None,
            }
            mock_get_logto.return_value = mock_logto

            mock_user_repo = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = "user-123"
            mock_user.username = "testuser"
            mock_user.email = "test@example.com"
            mock_user.avatar_url = None
            mock_user.preferences = {}
            mock_user.default_model = "deepseek-v4-flash"
            mock_user.default_agent = "auto"
            mock_user.created_at = datetime.datetime.now(datetime.UTC)
            mock_user_repo.get_or_create_by_logto.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_session_repo = AsyncMock()
            mock_session_repo_class.return_value = mock_session_repo

            mock_jwt = MagicMock()
            mock_jwt.create_access_token.return_value = "test-access-token"
            mock_jwt.create_refresh_token.return_value = "test-refresh-token"
            mock_get_jwt.return_value = mock_jwt

            response = client.post(
                "/auth/logto/callback",
                json={
                    "code": "test-code",
                    "state": "test-state",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["access_token"] == "test-access-token"

    def test_logto_callback_validation_failure(self, client: TestClient, app):
        """测试 Logto 回调 - 验证失败."""
        with patch("src.routers.auth.get_logto_service") as mock_get_logto:
            mock_settings = MagicMock(spec=Settings)
            mock_settings.auth_enabled = True
            mock_settings.auth_mode = "logto"
            app.dependency_overrides[get_settings] = lambda: mock_settings

            mock_logto = AsyncMock()
            mock_logto.validate_callback.return_value = None
            mock_get_logto.return_value = mock_logto

            response = client.post(
                "/auth/logto/callback",
                json={
                    "code": "test-code",
                    "state": "test-state",
                },
            )

            assert response.status_code == 401

    def test_refresh_token_success(self, client: TestClient, app):
        """测试刷新令牌 - 成功."""
        with (
            patch("src.routers.auth.get_jwt_manager") as mock_get_jwt,
            patch("src.routers.auth.SessionRepository") as mock_session_repo_class,
            patch("src.routers.auth.UserRepository") as mock_user_repo_class,
        ):

            mock_settings = MagicMock(spec=Settings)
            mock_settings.auth_enabled = True
            mock_settings.auth_mode = "logto"
            app.dependency_overrides[get_settings] = lambda: mock_settings

            mock_jwt = MagicMock()
            mock_jwt.refresh_access_token.return_value = {
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
                "token_type": "Bearer",
                "expires_in": 7200,
            }
            mock_get_jwt.return_value = mock_jwt

            mock_session_repo = AsyncMock()
            mock_session = MagicMock()
            mock_session.user_id = "user-123"
            mock_session_repo.get_by_refresh_token.return_value = mock_session
            mock_session_repo_class.return_value = mock_session_repo

            mock_user_repo = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = "user-123"
            mock_user.username = "testuser"
            mock_user.email = "test@example.com"
            mock_user.avatar_url = None
            mock_user.preferences = {}
            mock_user.default_model = "deepseek-v4-flash"
            mock_user.default_agent = "auto"
            mock_user.created_at = datetime.datetime.now(datetime.UTC)
            mock_user_repo.get_by_id.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            response = client.post(
                "/auth/refresh",
                json={
                    "refresh_token": "old-refresh-token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["access_token"] == "new-access-token"

    def test_refresh_token_invalid(self, client: TestClient, app):
        """测试刷新令牌 - 无效令牌."""
        with patch("src.routers.auth.get_jwt_manager") as mock_get_jwt:
            mock_settings = MagicMock(spec=Settings)
            mock_settings.auth_enabled = True
            app.dependency_overrides[get_settings] = lambda: mock_settings

            mock_jwt = MagicMock()
            mock_jwt.refresh_access_token.return_value = None
            mock_get_jwt.return_value = mock_jwt

            response = client.post(
                "/auth/refresh",
                json={
                    "refresh_token": "invalid-token",
                },
            )

            assert response.status_code == 401

    def test_logout_success(self, client: TestClient, app):
        """测试登出 - 成功."""
        with patch("src.routers.auth.SessionRepository") as mock_session_repo_class:
            mock_settings = MagicMock(spec=Settings)
            mock_settings.auth_enabled = True
            app.dependency_overrides[get_settings] = lambda: mock_settings

            mock_session_repo = AsyncMock()
            mock_session_repo.delete_by_refresh_token.return_value = True
            mock_session_repo_class.return_value = mock_session_repo

            response = client.post(
                "/auth/logout",
                json={
                    "refresh_token": "test-refresh-token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["deleted"] is True

    def test_logout_auth_disabled(self, client: TestClient, app):
        """测试登出 - 认证关闭."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = False
        app.dependency_overrides[get_settings] = lambda: mock_settings

        response = client.post(
            "/auth/logout",
            json={
                "refresh_token": "test-refresh-token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "no session to logout" in data["data"]["message"]

    def test_get_me_success(self, client: TestClient, app):
        """测试获取当前用户信息 - 成功."""
        from src.services.auth import get_current_user

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            avatar_url=None,
            preferences={},
            default_model="deepseek-v4-flash",
            default_agent="auto",
            created_at=datetime.datetime.now(datetime.UTC),
        )
        app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == "user-123"
        assert data["data"]["username"] == "testuser"

    def test_get_me_unauthorized(self, client: TestClient, app):
        """测试获取当前用户信息 - 未认证."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_get_me_forward_auth_real_dependency(self, client: TestClient, app):
        """测试获取当前用户信息 - 真实 forward-auth 依赖链路 (不 mock get_current_user)."""
        app.dependency_overrides.clear()

        # 模拟 Settings 为 forward-auth 模式
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = True
        mock_settings.auth_mode = "forward-auth"
        mock_settings.default_model = "gemini-3.8-flash"
        app.dependency_overrides[get_settings] = lambda: mock_settings

        mock_repo = AsyncMock()
        mock_user = User(
            id="usr_live_test",
            username="jason_dev",
            email="jason@hsbc.com",
            avatar_url="https://github.com/jason_dev.png",
            preferences={},
            default_model="gemini-3.8-flash",
            default_agent="auto",
            created_at=datetime.datetime.now(datetime.UTC),
        )
        mock_repo.get_or_create_by_sso.return_value = mock_user

        with patch("src.services.auth.UserRepository", return_value=mock_repo):
            response = client.get(
                "/auth/me",
                headers={
                    "X-Auth-Request-User": "usr_live_test",
                    "X-Auth-Request-Preferred-Username": "jason_dev",
                    "X-Auth-Request-Email": "jason@hsbc.com",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["id"] == "usr_live_test"
            assert data["data"]["username"] == "jason_dev"
            assert data["data"]["avatar_url"] == "https://github.com/jason_dev.png"
