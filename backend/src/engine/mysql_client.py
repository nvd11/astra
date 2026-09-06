"""MySQL HeatWave 异步客户端模块.

基于 SQLAlchemy 2.0 + asyncmy 提供连接池与事务管理.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.configs.config import get_settings


class MySQLClient:
    """MySQL HeatWave 异步连接池与事务管理器."""

    def __init__(self, database_url: str) -> None:
        """初始化 MySQL 异步引擎.

        Args:
            database_url: 数据库连接串 (mysql+asyncmy://...)
        """
        self._engine: AsyncEngine = create_async_engine(
            database_url,
            pool_size=20,
            max_overflow=10,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info(f"MySQL client initialized: {database_url.split('@')[-1]}")

    async def check_connection(self) -> bool:
        """验证数据库连通性.

        Returns:
            bool: 连接是否成功
        """
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("MySQL connection check passed")
            return True
        except Exception as e:
            logger.error(f"MySQL connection check failed: {e}")
            return False

    @asynccontextmanager
    async def session_scope(self) -> AsyncIterator[AsyncSession]:
        """事务上下文管理器，自动提交或回滚.

        Yields:
            AsyncSession: 数据库会话
        """
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        """优雅关闭连接池."""
        await self._engine.dispose()
        logger.info("MySQL connection pool closed")


# 全局单例
_mysql_client: MySQLClient | None = None


def get_mysql_client() -> MySQLClient:
    """获取 MySQL 客户端单例.

    Returns:
        MySQLClient: 数据库客户端实例
    """
    global _mysql_client
    if _mysql_client is None:
        settings = get_settings()
        _mysql_client = MySQLClient(settings.database_url)
    return _mysql_client


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖注入：获取数据库会话.

    Yields:
        AsyncSession: 数据库会话
    """
    client = get_mysql_client()
    async with client.session_scope() as session:
        yield session
