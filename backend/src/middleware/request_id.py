"""全链路 Request ID 追踪中间件.

自动提取或生成 UUID 标识，绑定至 Loguru 日志上下文，并回填至 Response Headers.
"""

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求唯一追踪 ID 中间件."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """拦截请求注入 request_id."""
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # 绑定到 loguru 上下文变量
        with logger.contextualize(request_id=request_id):
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
