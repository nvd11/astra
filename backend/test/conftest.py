"""pytest 全局 fixtures 配置."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# 在导入应用前设置测试环境变量
os.environ["APP_ENVIRONMENT"] = "local"
os.environ["APP_DATABASE_URL"] = "mysql+asyncmy://test:test@localhost:3306/test"
os.environ["APP_REDIS_URL"] = "redis://localhost:6379/1"
os.environ["APP_JWT_SECRET"] = "test-secret-key-for-pytest-only"
os.environ["APP_LITELLM_API_KEY"] = "sk-test-litellm-key"
os.environ["APP_LOGTO_APP_ID"] = "test-logto-app-id"
os.environ["APP_LOGTO_APP_SECRET"] = "test-logto-app-secret"


@pytest.fixture(scope="session")
def anyio_backend():
    """配置 anyio 后端."""
    return "asyncio"


@pytest.fixture
def mock_settings():
    """Mock Settings 配置."""
    from src.configs.config import Settings

    return Settings(
        app_name="Astra-Test",
        app_version="1.0.0-test",
        app_environment="local",
        debug=True,
        host="127.0.0.1",
        port=8000,
        workers=1,
        root_path="",
        log_level="DEBUG",
        database_url="mysql+asyncmy://test:test@localhost:3306/test",
        redis_url="redis://localhost:6379/1",
        litellm_base_url="https://litellm.test.local",
        litellm_api_key="sk-test-key",
        default_model="deepseek-v4-flash",
        jwt_secret="test-secret-key",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=120,
        jwt_refresh_token_expire_days=7,
        logto_endpoint="https://auth.test.local",
        logto_app_id="test-app-id",
        logto_app_secret="test-app-secret",
        logto_redirect_uri="http://localhost:5173/callback",
    )


@pytest.fixture
def mock_mysql_client():
    """Mock MySQL 客户端."""
    client = MagicMock()
    client.check_connection = AsyncMock(return_value=True)
    client.close = AsyncMock()
    client.session_scope = MagicMock()
    return client


@pytest.fixture
def mock_redis_client():
    """Mock Redis 客户端."""
    client = MagicMock()
    client.ping = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.exists = AsyncMock(return_value=False)
    client.rpush = AsyncMock(return_value=1)
    client.lrange = AsyncMock(return_value=[])
    client.expire = AsyncMock(return_value=True)
    client.close = AsyncMock()
    return client


@pytest.fixture
def app(mock_mysql_client, mock_redis_client):
    """创建测试应用实例，注入 Mock 存储引擎."""
    with (
        patch("src.main.get_mysql_client", return_value=mock_mysql_client),
        patch("src.main.get_redis_client", return_value=mock_redis_client),
        patch("src.routers.health.get_mysql_client", return_value=mock_mysql_client),
        patch("src.routers.health.get_redis_client", return_value=mock_redis_client),
    ):
        from src.main import create_app

        app = create_app()

        # Mock get_db_session 以避免真实数据库连接
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.delete = AsyncMock()

        # 配置 execute 返回值的 scalars() 方法
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_result)
        mock_result.all = MagicMock(return_value=[])
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute.return_value = mock_result

        async def mock_get_db_session():
            yield mock_session

        from src.engine.mysql_client import get_db_session

        app.dependency_overrides[get_db_session] = mock_get_db_session

        yield app

        # 清理依赖覆盖
        app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """创建测试客户端."""
    return TestClient(app)


@pytest.fixture
def async_client(app):
    """创建异步测试客户端."""
    from httpx import ASGITransport, AsyncClient

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
