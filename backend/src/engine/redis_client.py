"""Redis 异步客户端模块.

基于 redis.asyncio 提供连接池与常用缓存操作.
"""

import redis.asyncio as aioredis
from loguru import logger

from src.configs.config import get_settings


class RedisClient:
    """Redis 异步客户端包装器."""

    def __init__(self, redis_url: str) -> None:
        """初始化 Redis 连接池.

        Args:
            redis_url: Redis 连接串 (redis://:password@host:port/db)
        """
        self._client = aioredis.from_url(
            redis_url,
            decode_responses=True,
            max_connections=20,
        )
        logger.info(f"Redis client initialized: {redis_url.split('@')[-1]}")

    async def get(self, key: str) -> str | None:
        """读取字符串缓存.

        Args:
            key: 缓存键

        Returns:
            str | None: 缓存值
        """
        return await self._client.get(key)

    async def set(self, key: str, value: str, expire: int | None = None) -> bool:
        """写入缓存.

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间 (秒)

        Returns:
            bool: 是否成功
        """
        return await self._client.set(key, value, ex=expire)

    async def setex(self, key: str, seconds: int, value: str) -> bool:
        """写入带 TTL 的缓存.

        Args:
            key: 缓存键
            seconds: 过期时间 (秒)
            value: 缓存值

        Returns:
            bool: 是否成功
        """
        return await self._client.setex(key, seconds, value)

    async def delete(self, *keys: str) -> int:
        """删除缓存.

        Args:
            *keys: 缓存键列表

        Returns:
            int: 删除数量
        """
        return await self._client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """检查键是否存在.

        Args:
            key: 缓存键

        Returns:
            bool: 是否存在
        """
        return await self._client.exists(key) > 0

    async def rpush(self, key: str, *values: str) -> int:
        """向列表末尾追加元素.

        Args:
            key: 列表键
            *values: 元素列表

        Returns:
            int: 列表长度
        """
        return await self._client.rpush(key, *values)

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        """读取列表区间.

        Args:
            key: 列表键
            start: 起始索引
            end: 结束索引

        Returns:
            list[str]: 元素列表
        """
        return await self._client.lrange(key, start, end)

    async def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间.

        Args:
            key: 缓存键
            seconds: 过期时间 (秒)

        Returns:
            bool: 是否成功
        """
        return await self._client.expire(key, seconds)

    async def incr(self, key: str) -> int:
        """数值自增 1.

        Args:
            key: 缓存键

        Returns:
            int: 自增后的数值
        """
        return await self._client.incr(key)

    async def ping(self) -> bool:
        """探活检测.

        Returns:
            bool: 是否连通
        """
        try:
            return await self._client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    async def close(self) -> None:
        """关闭连接池."""
        await self._client.aclose()
        logger.info("Redis connection pool closed")


# 全局单例
_redis_client: RedisClient | None = None


def get_redis_client() -> RedisClient:
    """获取 Redis 客户端单例.

    Returns:
        RedisClient: 缓存客户端实例
    """
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = RedisClient(settings.redis_url)
    return _redis_client
