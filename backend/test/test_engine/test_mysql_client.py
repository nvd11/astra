"""MySQL 客户端测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.engine.mysql_client import MySQLClient, get_db_session, get_mysql_client


class TestMySQLClient:
    """MySQL 客户端测试类."""

    def test_init(self):
        """测试 MySQLClient 初始化."""
        client = MySQLClient("mysql+asyncmy://user:pass@localhost:3306/test")
        assert client._engine is not None
        assert isinstance(client._engine, AsyncEngine)
        assert client._session_factory is not None

    @pytest.mark.asyncio
    async def test_check_connection_success(self):
        """测试数据库连接检查 - 成功."""
        client = MySQLClient("mysql+asyncmy://user:pass@localhost:3306/test")

        with patch("src.engine.mysql_client.create_async_engine") as mock_create_engine:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_conn
            mock_create_engine.return_value = mock_engine

            # 重新初始化以应用 mock
            client._engine = mock_engine
            result = await client.check_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_check_connection_failure(self):
        """测试数据库连接检查 - 失败."""
        client = MySQLClient("mysql+asyncmy://user:pass@localhost:3306/test")

        with patch("src.engine.mysql_client.create_async_engine") as mock_create_engine:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_engine.connect.side_effect = Exception("Connection refused")
            mock_create_engine.return_value = mock_engine

            # 重新初始化以应用 mock
            client._engine = mock_engine
            result = await client.check_connection()
            assert result is False

    @pytest.mark.asyncio
    async def test_session_scope_commit(self):
        """测试事务上下文 - 正常提交."""
        client = MySQLClient("mysql+asyncmy://user:pass@localhost:3306/test")

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        with patch.object(client, "_session_factory", return_value=mock_session):
            async with client.session_scope() as session:
                assert session is mock_session

            mock_session.commit.assert_called_once()
            mock_session.rollback.assert_not_called()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_scope_rollback(self):
        """测试事务上下文 - 异常回滚."""
        client = MySQLClient("mysql+asyncmy://user:pass@localhost:3306/test")

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        with patch.object(client, "_session_factory", return_value=mock_session):
            with pytest.raises(ValueError):
                async with client.session_scope():
                    raise ValueError("Test error")

            mock_session.commit.assert_not_called()
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self):
        """测试关闭连接池."""
        client = MySQLClient("mysql+asyncmy://user:pass@localhost:3306/test")

        with patch("src.engine.mysql_client.create_async_engine") as mock_create_engine:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_engine.dispose = AsyncMock()
            mock_create_engine.return_value = mock_engine

            # 重新初始化以应用 mock
            client._engine = mock_engine
            await client.close()
            mock_engine.dispose.assert_called_once()


class TestGetMySQLClient:
    """get_mysql_client 单例测试类."""

    def test_get_mysql_client_singleton(self):
        """测试单例模式."""
        with patch("src.engine.mysql_client.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.database_url = "mysql+asyncmy://test:test@localhost:3306/test"
            mock_get_settings.return_value = mock_settings

            # 重置全局单例
            import src.engine.mysql_client as mysql_module

            mysql_module._mysql_client = None

            client1 = get_mysql_client()
            client2 = get_mysql_client()
            assert client1 is client2


class TestGetDbSession:
    """get_db_session 依赖注入测试类."""

    @pytest.mark.asyncio
    async def test_get_db_session(self):
        """测试数据库会话依赖注入."""
        mock_client = MagicMock()
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        mock_client.session_scope = MagicMock()
        mock_client.session_scope.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_client.session_scope.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.engine.mysql_client.get_mysql_client", return_value=mock_client
        ):
            async for session in get_db_session():
                assert session is mock_session
