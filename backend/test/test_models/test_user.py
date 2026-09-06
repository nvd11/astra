"""用户模型与仓库测试."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import SessionRepository, User, UserRepository, UserSession


class TestUserRepository:
    """用户仓库测试类."""

    @pytest.fixture
    def mock_session(self):
        """创建 Mock 数据库会话."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def user_repo(self, mock_session):
        """创建用户仓库实例."""
        return UserRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_id(self, user_repo, mock_session):
        """测试根据 ID 查询用户."""
        mock_user = MagicMock(spec=User)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = await user_repo.get_by_id("user-123")
        assert result is mock_user

    @pytest.mark.asyncio
    async def test_get_by_username(self, user_repo, mock_session):
        """测试根据用户名查询用户."""
        mock_user = MagicMock(spec=User)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = await user_repo.get_by_username("testuser")
        assert result is mock_user

    @pytest.mark.asyncio
    async def test_get_by_logto_id(self, user_repo, mock_session):
        """测试根据 Logto ID 查询用户."""
        mock_user = MagicMock(spec=User)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = await user_repo.get_by_logto_id("logto-123")
        assert result is mock_user

    @pytest.mark.asyncio
    async def test_create(self, user_repo, mock_session):
        """测试创建用户."""
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        user = await user_repo.create(
            username="testuser",
            email="test@example.com",
            avatar_url="https://example.com/avatar.png",
            logto_id="logto-123",
            preferences={"theme": "dark"},
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update(self, user_repo, mock_session):
        """测试更新用户."""
        mock_user = MagicMock(spec=User)
        mock_user.id = "user-123"
        mock_user.username = "oldname"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        result = await user_repo.update("user-123", username="newname")

        assert result is mock_user
        assert mock_user.username == "newname"

    @pytest.mark.asyncio
    async def test_update_not_found(self, user_repo, mock_session):
        """测试更新不存在的用户."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await user_repo.update("user-123", username="newname")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_or_create_by_logto_existing(self, user_repo, mock_session):
        """测试根据 Logto 获取或创建用户 - 已存在."""
        mock_user = MagicMock(spec=User)
        mock_user.id = "user-123"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        result = await user_repo.get_or_create_by_logto(
            logto_id="logto-123",
            username="testuser",
            email="test@example.com",
        )

        assert result is mock_user

    @pytest.mark.asyncio
    async def test_get_or_create_by_logto_new(self, user_repo, mock_session):
        """测试根据 Logto 获取或创建用户 - 新建."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        result = await user_repo.get_or_create_by_logto(
            logto_id="logto-123",
            username="testuser",
            email="test@example.com",
        )

        assert result.username == "testuser"
        assert result.logto_id == "logto-123"


class TestSessionRepository:
    """会话仓库测试类."""

    @pytest.fixture
    def mock_session(self):
        """创建 Mock 数据库会话."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def session_repo(self, mock_session):
        """创建会话仓库实例."""
        return SessionRepository(mock_session)

    @pytest.mark.asyncio
    async def test_create(self, session_repo, mock_session):
        """测试创建会话."""
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        expires_at = datetime.now(UTC)
        session = await session_repo.create(
            user_id="user-123",
            refresh_token="test-refresh-token",
            device_info="Test Device",
            ip_address="127.0.0.1",
            expires_at=expires_at,
        )

        assert session.user_id == "user-123"
        assert session.refresh_token == "test-refresh-token"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_refresh_token(self, session_repo, mock_session):
        """测试根据 Refresh Token 查询会话."""
        mock_user_session = MagicMock(spec=UserSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user_session
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_by_refresh_token("test-token")
        assert result is mock_user_session

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, session_repo, mock_session):
        """测试查询用户所有会话."""
        mock_sessions = [MagicMock(spec=UserSession), MagicMock(spec=UserSession)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_sessions
        mock_session.execute.return_value = mock_result

        result = await session_repo.get_by_user_id("user-123")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete_by_refresh_token(self, session_repo, mock_session):
        """测试根据 Refresh Token 删除会话."""
        mock_user_session = MagicMock(spec=UserSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user_session
        mock_session.execute.return_value = mock_result
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()

        result = await session_repo.delete_by_refresh_token("test-token")
        assert result is True
        mock_session.delete.assert_called_once_with(mock_user_session)

    @pytest.mark.asyncio
    async def test_delete_by_refresh_token_not_found(self, session_repo, mock_session):
        """测试删除不存在的会话."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await session_repo.delete_by_refresh_token("test-token")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_by_user_id(self, session_repo, mock_session):
        """测试删除用户所有会话."""
        mock_session1 = MagicMock(spec=UserSession)
        mock_session1.refresh_token = "token-1"
        mock_session2 = MagicMock(spec=UserSession)
        mock_session2.refresh_token = "token-2"
        mock_sessions = [mock_session1, mock_session2]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_sessions
        mock_session.execute.return_value = mock_result
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()

        count = await session_repo.delete_by_user_id(
            "user-123", exclude_current="token-1"
        )
        assert count == 1
        mock_session.delete.assert_called_once_with(mock_session2)
