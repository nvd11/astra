"""速率限制中间件 (基于 Redis 滑动窗口/计数器).

对未受信任来源或各 IP 实施请求限流，保障高并发服务稳定性.
"""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from src.engine.redis_client import get_redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis 计数器访问限流中间件."""

    def __init__(
        self, app: Any, max_requests: int = 120, window_seconds: int = 60
    ) -> None:
        """初始化限流配置.

        Args:
            app: ASGI 应用实例
            max_requests: 窗口内最大请求数 (默认 120 次/分钟)
            window_seconds: 时间窗口长度 (秒)
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.whitelist_prefixes = (
            "/health",
            "/ready",
            "/live",
            "/docs",
            "/redoc",
            "/openapi.json",
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """执行限流校验."""
        path = request.url.path

        # 白名单跳过
        if any(path.startswith(prefix) for prefix in self.whitelist_prefixes):
            return await call_next(request)

        # 获取限流主体 (客户端 IP 或 JWT 携带的 sub)
        identifier = "unknown"
        if request.client:
            identifier = request.client.host

        current_window = int(time.time() // self.window_seconds)
        redis_key = f"rate_limit:{identifier}:{current_window}"

        try:
            redis = get_redis_client()
            count = await redis.incr(redis_key)
            if count == 1:
                await redis.expire(redis_key, self.window_seconds + 5)

            if count > self.max_requests:
                logger.warning(
                    f"Rate limit exceeded for {identifier} on {path}: {count}/{self.max_requests}"
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": 429,
                        "message": f"Too Many Requests. Maximum {self.max_requests} requests per minute.",
                        "data": None,
                    },
                    headers={"Retry-After": str(self.window_seconds)},
                )
        except Exception as e:
            # 优雅降级 (Fail Open)：若 Redis 短暂不可用，不阻断正常业务
            logger.debug(f"Rate limiter fail-open: {e}")

        return await call_next(request)
