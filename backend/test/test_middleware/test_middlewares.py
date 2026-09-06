"""中间件单元与集成测试."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.request_id import RequestIDMiddleware
from src.middleware.timing import TimingMiddleware


class TestMiddlewares:
    """中间件测试套件."""

    @pytest.fixture
    def test_app(self):
        """构造带有所有中间件的独立测试 App."""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, max_requests=2, window_seconds=60)
        app.add_middleware(TimingMiddleware)
        app.add_middleware(RequestIDMiddleware)

        @app.get("/ping")
        async def ping():
            return {"msg": "pong"}

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        return app

    def test_request_id_generated(self, test_app):
        """测试自动生成 Request ID."""
        client = TestClient(test_app)
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 10

    def test_request_id_forwarded(self, test_app):
        """测试透传上游传入的 Request ID."""
        client = TestClient(test_app)
        custom_id = "custom-trace-uuid-12345"
        response = client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == custom_id

    def test_timing_middleware(self, test_app):
        """测试耗时头注入."""
        client = TestClient(test_app)
        response = client.get("/ping")
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        assert response.headers["X-Process-Time"].endswith("ms")

    def test_rate_limit_whitelist(self, test_app):
        """测试白名单路径跳过限流计数."""
        client = TestClient(test_app)
        for _ in range(5):
            res = client.get("/health")
            assert res.status_code == 200

    def test_rate_limit_exceeded(self, test_app):
        """测试触发 429 请求超限."""
        client = TestClient(test_app)

        mock_redis = AsyncMock()
        # 模拟计数器：前两次放行，第三次超限
        mock_redis.incr = AsyncMock(side_effect=[1, 2, 3])
        mock_redis.expire = AsyncMock()

        with patch(
            "src.middleware.rate_limit.get_redis_client", return_value=mock_redis
        ):
            res1 = client.get("/ping")
            assert res1.status_code == 200

            res2 = client.get("/ping")
            assert res2.status_code == 200

            # 第三次请求超限
            res3 = client.get("/ping")
            assert res3.status_code == 429
            data = res3.json()
            assert data["code"] == 429
            assert "Too Many Requests" in data["message"]
            assert "Retry-After" in res3.headers

    def test_rate_limit_fail_open(self, test_app):
        """测试 Redis 故障时降级放行 (Fail Open)."""
        client = TestClient(test_app)

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(side_effect=RuntimeError("Redis connection down"))

        with patch(
            "src.middleware.rate_limit.get_redis_client", return_value=mock_redis
        ):
            res = client.get("/ping")
            assert res.status_code == 200
