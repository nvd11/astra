"""Redis L1 会话上下文短期记忆缓存 (Cache-Aside 模式).

在用户多轮对话时优先从 Redis 读取最近 N 轮上下文，大幅降低对 MySQL 的网络与磁盘 IO.
支持缓存失效 (Cache Invalidation)、TTL 自动续期与 Fail-Open 优雅降级.
"""

import json
from typing import Any

from loguru import logger

from src.engine.redis_client import RedisClient, get_redis_client


class ShortTermMemory:
    """基于 Redis 的短期多轮对话上下文缓存."""

    def __init__(
        self, redis_client: RedisClient | None = None, default_ttl: int = 1800
    ) -> None:
        """初始化短期记忆缓存.

        Args:
            redis_client: Redis 客户端实例
            default_ttl: 缓存生存周期 (秒)，默认 30 分钟 (1800s)
        """
        self._redis = redis_client
        self.default_ttl = default_ttl

    def _get_client(self) -> RedisClient:
        """获取 Redis 客户端单例."""
        if self._redis is not None:
            return self._redis
        return get_redis_client()

    def _get_key(self, conversation_id: str) -> str:
        """生成会话上下文缓存键."""
        return f"conv:{conversation_id}:context"

    async def get_context(self, conversation_id: str) -> list[dict[str, str]] | None:
        """从 Redis 读取多轮对话上下文.

        Args:
            conversation_id: 会话 ID

        Returns:
            list[dict[str, str]] | None: 命中的消息列表，未命中或故障返回 None
        """
        key = self._get_key(conversation_id)
        try:
            client = self._get_client()
            raw_data = await client.get(key)
            if not raw_data:
                logger.debug(f"L1 Cache miss for conv={conversation_id}")
                return None

            messages: list[dict[str, str]] = json.loads(raw_data)
            logger.debug(
                f"L1 Cache hit for conv={conversation_id}, msgs_len={len(messages)}"
            )
            return messages
        except Exception as err:
            logger.warning(f"L1 Cache read error (fail-open to MySQL): {err}")
            return None

    async def set_context(
        self,
        conversation_id: str,
        messages: list[dict[str, str]],
        ttl: int | None = None,
    ) -> bool:
        """写入/刷新会话上下文缓存.

        Args:
            conversation_id: 会话 ID
            messages: 上下文消息列表
            ttl: 过期时间 (秒)

        Returns:
            bool: 是否写入成功
        """
        key = self._get_key(conversation_id)
        expire_seconds = ttl or self.default_ttl
        try:
            client = self._get_client()
            payload = json.dumps(messages, ensure_ascii=False)
            await client.setex(key, expire_seconds, payload)
            logger.debug(
                f"L1 Cache saved for conv={conversation_id}, ttl={expire_seconds}s"
            )
            return True
        except Exception as err:
            logger.warning(f"L1 Cache write error: {err}")
            return False

    async def append_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        max_messages: int = 20,
        ttl: int | None = None,
    ) -> None:
        """向已有缓存追加一条消息并刷新 TTL.

        Args:
            conversation_id: 会话 ID
            role: 消息角色 (user / assistant)
            content: 消息文本
            max_messages: 缓存保留的最大消息数 (滑动窗口)
            ttl: 过期时间 (秒)
        """
        messages = await self.get_context(conversation_id)
        if messages is None:
            # 缓存未建立，跳过追加，后续会在流毕或查询时自动回填
            return

        messages.append({"role": role, "content": content})
        # 维持滑动窗口长度
        if len(messages) > max_messages:
            messages = messages[-max_messages:]

        await self.set_context(conversation_id, messages, ttl=ttl)

    async def clear(self, conversation_id: str) -> bool:
        """主动失效/清除指定会话的缓存 (在编辑、删除消息时调用以维持一致性).

        Args:
            conversation_id: 会话 ID

        Returns:
            bool: 是否清除成功
        """
        key = self._get_key(conversation_id)
        try:
            client = self._get_client()
            await client.delete(key)
            logger.debug(f"L1 Cache cleared for conv={conversation_id}")
            return True
        except Exception as err:
            logger.warning(f"L1 Cache clear error: {err}")
            return False


# 全局单例
_short_term_memory: ShortTermMemory | None = None


def get_short_term_memory() -> ShortTermMemory:
    """获取短期记忆缓存单例."""
    global _short_term_memory
    if _short_term_memory is None:
        _short_term_memory = ShortTermMemory()
    return _short_term_memory
