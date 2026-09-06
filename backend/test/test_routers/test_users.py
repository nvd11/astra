"""用户资料、偏好与用量统计路由单元测试."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.models.user import User
from src.services.auth import get_current_user


@pytest.fixture
def auth_user():
    """测试用已认证用户."""
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        avatar_url="https://example.com/avatar.png",
        preferences={"theme": "dark"},
        default_model="deepseek-v4-flash",
        default_agent="auto",
        created_at=datetime.datetime.now(datetime.UTC),
    )


class TestUsersRouter:
    """用户管理路由测试类."""

    def test_get_user_profile(self, client: TestClient, app, auth_user):
        """测试获取当前用户个人资料."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        response = client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == "user-123"
        assert data["data"]["username"] == "testuser"
        assert data["data"]["preferences"]["theme"] == "dark"

    def test_update_user_profile_success(self, client: TestClient, app, auth_user):
        """测试修改个人资料 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        updated_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            avatar_url="https://new-avatar.png",
            preferences={"theme": "light"},
            default_model="deepseek-v4-flash",
            default_agent="auto",
            created_at=datetime.datetime.now(datetime.UTC),
        )

        with patch("src.routers.users.UserRepository") as mock_user_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.update.return_value = updated_user
            mock_user_repo_cls.return_value = mock_repo

            response = client.put(
                "/users/me",
                json={
                    "avatar_url": "https://new-avatar.png",
                    "preferences": {"theme": "light"},
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["avatar_url"] == "https://new-avatar.png"
            assert data["data"]["preferences"]["theme"] == "light"

    def test_update_user_profile_not_found(self, client: TestClient, app, auth_user):
        """测试修改个人资料 - 用户不存在."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        with patch("src.routers.users.UserRepository") as mock_user_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.update.return_value = None
            mock_user_repo_cls.return_value = mock_repo

            response = client.put(
                "/users/me",
                json={"avatar_url": "https://avatar.png"},
            )
            assert response.status_code == 404

    def test_update_user_preferences_success(self, client: TestClient, app, auth_user):
        """测试修改模型与智能体偏好 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        updated_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            avatar_url=None,
            preferences={},
            default_model="deepseek-reasoner",
            default_agent="deep_reasoner",
            created_at=datetime.datetime.now(datetime.UTC),
        )

        with patch("src.routers.users.UserRepository") as mock_user_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.update.return_value = updated_user
            mock_user_repo_cls.return_value = mock_repo

            response = client.put(
                "/users/preferences",
                json={
                    "default_model": "deepseek-reasoner",
                    "default_agent": "deep_reasoner",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["default_model"] == "deepseek-reasoner"
            assert data["data"]["default_agent"] == "deep_reasoner"

    def test_update_user_preferences_not_found(
        self, client: TestClient, app, auth_user
    ):
        """测试修改模型与智能体偏好 - 用户不存在."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        with patch("src.routers.users.UserRepository") as mock_user_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.update.return_value = None
            mock_user_repo_cls.return_value = mock_repo

            response = client.put(
                "/users/preferences",
                json={"default_model": "deepseek-chat"},
            )
            assert response.status_code == 404

    def test_get_user_stats(self, client: TestClient, app, auth_user):
        """测试聚合获取用量统计."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        # Mock 数据库聚合查询结果
        mock_conv_count = MagicMock()
        mock_conv_count.scalar_one.return_value = 10

        mock_all_msg = MagicMock()
        mock_all_msg.one.return_value = (50, 15000)

        mock_today_msg = MagicMock()
        mock_today_msg.one.return_value = (8, 2400)

        # 重写 get_db_session 提供 mock execute 返回
        async def mock_db_session():
            session = AsyncMock()
            session.execute.side_effect = [
                mock_conv_count,
                mock_all_msg,
                mock_today_msg,
            ]
            yield session

        from src.engine.mysql_client import get_db_session

        app.dependency_overrides[get_db_session] = mock_db_session

        response = client.get("/users/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        stats = data["data"]
        assert stats["total_conversations"] == 10
        assert stats["total_messages"] == 50
        assert stats["total_tokens"] == 15000
        assert stats["today_messages"] == 8
        assert stats["today_tokens"] == 2400
