"""Redis 客户端测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.engine.redis_client import RedisClient, get_redis_client


class TestRedisClient:
    """Redis 客户端测试类."""

    def test_init(self):
        """测试 RedisClient 初始化."""
        client = RedisClient("redis://:password@localhost:6379/0")
        assert client._client is not None

    @pytest.mark.asyncio
    async def test_get(self):
        """测试读取缓存."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.get = AsyncMock(return_value="test_value")

        result = await client.get("test_key")
        assert result == "test_value"
        client._client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_set(self):
        """测试写入缓存."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.set = AsyncMock(return_value=True)

        result = await client.set("test_key", "test_value", expire=60)
        assert result is True
        client._client.set.assert_called_once_with("test_key", "test_value", ex=60)

    @pytest.mark.asyncio
    async def test_setex(self):
        """测试写入带 TTL 缓存."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.setex = AsyncMock(return_value=True)

        result = await client.setex("test_key", 60, "test_value")
        assert result is True
        client._client.setex.assert_called_once_with("test_key", 60, "test_value")

    @pytest.mark.asyncio
    async def test_delete(self):
        """测试删除缓存."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.delete = AsyncMock(return_value=2)

        result = await client.delete("key1", "key2")
        assert result == 2
        client._client.delete.assert_called_once_with("key1", "key2")

    @pytest.mark.asyncio
    async def test_exists_true(self):
        """测试键存在."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.exists = AsyncMock(return_value=1)

        result = await client.exists("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        """测试键不存在."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.exists = AsyncMock(return_value=0)

        result = await client.exists("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_rpush(self):
        """测试列表追加."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.rpush = AsyncMock(return_value=3)

        result = await client.rpush("test_list", "a", "b", "c")
        assert result == 3
        client._client.rpush.assert_called_once_with("test_list", "a", "b", "c")

    @pytest.mark.asyncio
    async def test_lrange(self):
        """测试列表读取."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.lrange = AsyncMock(return_value=["a", "b", "c"])

        result = await client.lrange("test_list", 0, -1)
        assert result == ["a", "b", "c"]
        client._client.lrange.assert_called_once_with("test_list", 0, -1)

    @pytest.mark.asyncio
    async def test_expire(self):
        """测试设置过期时间."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.expire = AsyncMock(return_value=True)

        result = await client.expire("test_key", 300)
        assert result is True
        client._client.expire.assert_called_once_with("test_key", 300)

    @pytest.mark.asyncio
    async def test_ping_success(self):
        """测试探活 - 成功."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.ping = AsyncMock(return_value=True)

        result = await client.ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_ping_failure(self):
        """测试探活 - 失败."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.ping = AsyncMock(side_effect=Exception("Connection refused"))

        result = await client.ping()
        assert result is False

    @pytest.mark.asyncio
    async def test_close(self):
        """测试关闭连接."""
        client = RedisClient("redis://localhost:6379/0")
        client._client.aclose = AsyncMock()

        await client.close()
        client._client.aclose.assert_called_once()


class TestGetRedisClient:
    """get_redis_client 单例测试类."""

    def test_get_redis_client_singleton(self):
        """测试单例模式."""
        with patch("src.engine.redis_client.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.redis_url = "redis://localhost:6379/0"
            mock_get_settings.return_value = mock_settings

            # 重置全局单例
            import src.engine.redis_client as redis_module

            redis_module._redis_client = None

            client1 = get_redis_client()
            client2 = get_redis_client()
            assert client1 is client2
