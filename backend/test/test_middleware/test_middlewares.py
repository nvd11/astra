"""中间件单元与集成测试."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.middleware.rate_limit import RateLimitMiddleware, extract_client_ip
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

    def test_extract_client_ip_priorities(self):
        """测试提取真实客户端 IP 的各级优先级."""
        from unittest.mock import MagicMock

        # 1. CF-Connecting-IP 优先
        req1 = MagicMock()
        req1.headers = {
            "CF-Connecting-IP": "104.16.1.1",
            "X-Forwarded-For": "10.0.0.1, 10.42.0.1",
            "X-Real-IP": "10.0.0.2",
        }
        assert extract_client_ip(req1) == "104.16.1.1"

        # 2. X-Forwarded-For 代理链第一项
        req2 = MagicMock()
        req2.headers = {
            "X-Forwarded-For": "203.0.113.195, 10.42.0.10",
            "X-Real-IP": "10.42.0.10",
        }
        assert extract_client_ip(req2) == "203.0.113.195"

        # 3. X-Real-IP
        req3 = MagicMock()
        req3.headers = {"X-Real-IP": "198.51.100.42"}
        assert extract_client_ip(req3) == "198.51.100.42"

        # 4. request.client.host 直连回退
        req4 = MagicMock()
        req4.headers = {}
        req4.client.host = "192.168.1.50"
        assert extract_client_ip(req4) == "192.168.1.50"

        # 5. 完全无法获取时回退 unknown
        req5 = MagicMock()
        req5.headers = {}
        req5.client = None
        assert extract_client_ip(req5) == "unknown"

    def test_rate_limit_per_client_ip_isolation(self, test_app):
        """测试不同客户端真实 IP 的限流键隔离."""
        client = TestClient(test_app)

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()

        with patch(
            "src.middleware.rate_limit.get_redis_client", return_value=mock_redis
        ):
            # 客户端 A
            client.get("/ping", headers={"CF-Connecting-IP": "1.1.1.1"})
            key_a = mock_redis.incr.call_args[0][0]
            assert "1.1.1.1" in key_a

            # 客户端 B
            client.get("/ping", headers={"CF-Connecting-IP": "2.2.2.2"})
            key_b = mock_redis.incr.call_args[0][0]
            assert "2.2.2.2" in key_b

            assert key_a != key_b
