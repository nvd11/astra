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


def extract_client_ip(request: Request) -> str:
    """提取客户端真实 IP 地址 (支持 Cloudflare、Kong/Nginx 及直连).

    优先级：
    1. CF-Connecting-IP (Cloudflare 边缘注入的真实访客 IP)
    2. X-Forwarded-For (反向代理链，取最左侧原始客户端 IP)
    3. X-Real-IP (反向代理直接指定的目标真实 IP)
    4. request.client.host (直连客户端 Socket IP)

    Args:
        request: FastAPI 请求对象

    Returns:
        str: 识别出的真实客户端 IP
    """
    # 1. Cloudflare 真实 IP
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip and cf_ip.strip():
        return cf_ip.strip()

    # 2. X-Forwarded-For 代理链第一位为原始客户端 IP
    xff = request.headers.get("X-Forwarded-For")
    if xff and xff.strip():
        client_ip = xff.split(",")[0].strip()
        if client_ip:
            return client_ip

    # 3. X-Real-IP
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip and x_real_ip.strip():
        return x_real_ip.strip()

    # 4. 直连客户端 host
    if request.client and request.client.host:
        return request.client.host

    return "unknown"


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

        # 获取限流主体 (真实客户端 IP)
        identifier = extract_client_ip(request)

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
