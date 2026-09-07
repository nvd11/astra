"""Redis L1 短期记忆上下文缓存单元测试."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.memory.short_term import ShortTermMemory, get_short_term_memory


class TestShortTermMemory:
    """短期记忆缓存测试类."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis 客户端."""
        client = AsyncMock()
        client.get = AsyncMock()
        client.setex = AsyncMock()
        client.delete = AsyncMock()
        return client

    @pytest.fixture
    def memory(self, mock_redis):
        """短期记忆实例."""
        return ShortTermMemory(redis_client=mock_redis, default_ttl=1800)

    @pytest.mark.asyncio
    async def test_get_context_miss(self, memory, mock_redis):
        """测试缓存未命中."""
        mock_redis.get.return_value = None
        result = await memory.get_context("conv-1")
        assert result is None
        mock_redis.get.assert_called_once_with("conv:conv-1:context")

    @pytest.mark.asyncio
    async def test_get_context_hit(self, memory, mock_redis):
        """测试缓存命中."""
        raw = json.dumps([{"role": "user", "content": "hello"}])
        mock_redis.get.return_value = raw

        result = await memory.get_context("conv-1")
        assert result == [{"role": "user", "content": "hello"}]

    @pytest.mark.asyncio
    async def test_get_context_fail_open_on_error(self, memory, mock_redis):
        """测试 Redis 异常时 Fail-Open 降级放行 (返回 None 由 MySQL 兜底)."""
        mock_redis.get.side_effect = RuntimeError("Redis connection error")

        result = await memory.get_context("conv-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_context_success(self, memory, mock_redis):
        """测试写入缓存."""
        msgs = [{"role": "user", "content": "hi"}]
        ok = await memory.set_context("conv-1", msgs, ttl=1200)

        assert ok is True
        mock_redis.setex.assert_called_once_with(
            "conv:conv-1:context", 1200, json.dumps(msgs, ensure_ascii=False)
        )

    @pytest.mark.asyncio
    async def test_set_context_error(self, memory, mock_redis):
        """测试写入异常时安全返回 False."""
        mock_redis.setex.side_effect = RuntimeError("Redis down")
        ok = await memory.set_context("conv-1", [])
        assert ok is False

    @pytest.mark.asyncio
    async def test_append_message_existing_and_sliding_window(self, memory, mock_redis):
        """测试追加消息并维持滑动窗口最大消息数."""
        initial_msgs = [{"role": f"user_{i}", "content": f"msg_{i}"} for i in range(5)]
        mock_redis.get.return_value = json.dumps(initial_msgs)

        await memory.append_message(
            conversation_id="conv-1",
            role="assistant",
            content="latest_reply",
            max_messages=4,  # 最多保留 4 条
            ttl=1800,
        )

        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        saved_msgs = json.loads(args[2])
        assert len(saved_msgs) == 4
        assert saved_msgs[-1] == {"role": "assistant", "content": "latest_reply"}

    @pytest.mark.asyncio
    async def test_append_message_no_existing_cache(self, memory, mock_redis):
        """测试无已有缓存时安全跳过追加."""
        mock_redis.get.return_value = None
        await memory.append_message("conv-1", "user", "hello")
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear(self, memory, mock_redis):
        """测试主动清除失效会话缓存."""
        ok = await memory.clear("conv-1")
        assert ok is True
        mock_redis.delete.assert_called_once_with("conv:conv-1:context")

    @pytest.mark.asyncio
    async def test_clear_error(self, memory, mock_redis):
        """测试清除缓存发生异常时安全返回 False."""
        mock_redis.delete.side_effect = RuntimeError("Redis error")
        ok = await memory.clear("conv-1")
        assert ok is False


class TestGetShortTermMemory:
    """单例获取器测试."""

    def test_singleton(self):
        """测试单例获取."""
        import src.memory.short_term as m
        m._short_term_memory = None

        m1 = get_short_term_memory()
        m2 = get_short_term_memory()
        assert m1 is m2
