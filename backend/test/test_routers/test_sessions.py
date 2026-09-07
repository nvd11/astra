"""会话管理路由测试."""

import datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from src.configs.config import Settings, get_settings
from src.models.user import User, UserSession
from src.services.auth import get_current_user


class TestSessionsRouter:
    """会话管理路由测试类."""

    def test_list_sessions_success(self, client: TestClient, app):
        """测试获取会话列表 - 成功."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

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

        mock_session_repo = AsyncMock()
        mock_session = MagicMock(spec=UserSession)
        mock_session.id = "session-123"
        mock_session.device_info = "Test Device"
        mock_session.ip_address = "127.0.0.1"
        mock_session.last_active_at = datetime.datetime.now(datetime.UTC)
        mock_session.expires_at = datetime.datetime.now(datetime.UTC)
        mock_session_repo.get_by_user_id.return_value = [mock_session]

        from unittest.mock import patch

        with patch(
            "src.routers.sessions.SessionRepository", return_value=mock_session_repo
        ):
            response = client.get("/sessions", headers={"X-Session-ID": "session-123"})

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert len(data["data"]) == 1
            assert data["data"][0]["device_info"] == "Test Device"
            assert data["data"][0]["is_current"] is True

    def test_list_sessions_auth_disabled(self, client: TestClient, app):
        """测试获取会话列表 - 认证关闭."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = False
        app.dependency_overrides[get_settings] = lambda: mock_settings

        mock_user = User(
            id="anonymous",
            username="anonymous",
            email=None,
            avatar_url=None,
            preferences={},
            default_model="deepseek-v4-flash",
            default_agent="auto",
            created_at=datetime.datetime.now(datetime.UTC),
        )
        app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.get("/sessions")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    def test_delete_session_success(self, client: TestClient, app):
        """测试删除会话 - 成功."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

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

        mock_session_repo = AsyncMock()
        mock_session_repo.delete_by_id.return_value = True

        from unittest.mock import patch

        with patch(
            "src.routers.sessions.SessionRepository", return_value=mock_session_repo
        ):
            response = client.delete("/sessions/session-123")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            mock_session_repo.delete_by_id.assert_called_once_with(
                "session-123", "user-123"
            )

    def test_delete_session_not_found(self, client: TestClient, app):
        """测试删除会话 - 不存在."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

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

        mock_session_repo = AsyncMock()
        mock_session_repo.delete_by_id.return_value = False

        from unittest.mock import patch

        with patch(
            "src.routers.sessions.SessionRepository", return_value=mock_session_repo
        ):
            response = client.delete("/sessions/nonexistent")

            assert response.status_code == 404
            mock_session_repo.delete_by_id.assert_called_once_with(
                "nonexistent", "user-123"
            )

    def test_delete_session_auth_disabled(self, client: TestClient, app):
        """测试删除会话 - 认证关闭."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = False
        app.dependency_overrides[get_settings] = lambda: mock_settings

        mock_user = User(
            id="anonymous",
            username="anonymous",
            email=None,
            avatar_url=None,
            preferences={},
            default_model="deepseek-v4-flash",
            default_agent="auto",
            created_at=datetime.datetime.now(datetime.UTC),
        )
        app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.delete("/sessions/session-123")
        assert response.status_code == 403

    def test_delete_all_sessions_success(self, client: TestClient, app):
        """测试删除所有会话 - 成功."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

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

        mock_session_repo = AsyncMock()
        mock_session_repo.delete_by_user_id.return_value = 3

        from unittest.mock import patch

        with patch(
            "src.routers.sessions.SessionRepository", return_value=mock_session_repo
        ):
            response = client.delete("/sessions")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["count"] == 3

    def test_delete_all_sessions_auth_disabled(self, client: TestClient, app):
        """测试删除所有会话 - 认证关闭."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.auth_enabled = False
        app.dependency_overrides[get_settings] = lambda: mock_settings

        mock_user = User(
            id="anonymous",
            username="anonymous",
            email=None,
            avatar_url=None,
            preferences={},
            default_model="deepseek-v4-flash",
            default_agent="auto",
            created_at=datetime.datetime.now(datetime.UTC),
        )
        app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.delete("/sessions")
        assert response.status_code == 403
