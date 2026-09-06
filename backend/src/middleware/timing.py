"""请求耗时度量与访问日志中间件."""

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class TimingMiddleware(BaseHTTPMiddleware):
    """请求处理时间中间件."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """度量耗时并附带 X-Process-Time 头."""
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        process_time = (time.perf_counter() - start_time) * 1000.0  # 毫秒
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        # 过滤高频存活探针日志
        if request.url.path not in ("/live",):
            logger.info(
                f"{request.method} {request.url.path} status={response.status_code} duration={process_time:.2f}ms"
            )

        return response
