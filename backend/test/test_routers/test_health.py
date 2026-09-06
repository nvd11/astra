"""健康检查路由测试."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient


class TestHealthRouter:
    """健康检查路由测试类."""

    def test_health_check_success(self, client: TestClient):
        """测试健康检查端点 - 存储全部正常."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "success"
        assert data["data"]["status"] == "ok"
        assert data["data"]["service"] == "Astra"
        assert data["data"]["version"] == "1.0.0"
        assert data["data"]["mysql_ok"] is True
        assert data["data"]["redis_ok"] is True
        assert data["data"]["uptime_seconds"] is None
        assert "timestamp" in data

    def test_health_check_detailed(self, client: TestClient):
        """测试健康检查端点 - 详细模式."""
        response = client.get("/health?detailed=true")
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["status"] == "ok"
        assert data["data"]["uptime_seconds"] is not None
        assert isinstance(data["data"]["uptime_seconds"], float)

    def test_health_check_mysql_down(self, client: TestClient, mock_mysql_client):
        """测试健康检查端点 - MySQL 宕机."""
        mock_mysql_client.check_connection = AsyncMock(return_value=False)

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["status"] == "error"
        assert data["data"]["mysql_ok"] is False
        assert data["data"]["redis_ok"] is True

    def test_health_check_redis_down(self, client: TestClient, mock_redis_client):
        """测试健康检查端点 - Redis 宕机."""
        mock_redis_client.ping = AsyncMock(return_value=False)

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["status"] == "error"
        assert data["data"]["mysql_ok"] is True
        assert data["data"]["redis_ok"] is False

    def test_health_check_all_down(
        self, client: TestClient, mock_mysql_client, mock_redis_client
    ):
        """测试健康检查端点 - 全部存储宕机."""
        mock_mysql_client.check_connection = AsyncMock(return_value=False)
        mock_redis_client.ping = AsyncMock(return_value=False)

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["status"] == "error"
        assert data["data"]["mysql_ok"] is False
        assert data["data"]["redis_ok"] is False

    def test_readiness_check(self, client: TestClient):
        """测试就绪探针端点."""
        response = client.get("/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["status"] == "ok"
        assert data["data"]["mysql_ok"] is True
        assert data["data"]["redis_ok"] is True

    def test_liveness_check(self, client: TestClient):
        """测试存活探针端点."""
        response = client.get("/live")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["status"] == "ok"
        assert data["data"]["service"] == "Astra"
        assert data["data"]["version"] == "1.0.0"
        # 存活探针不检查存储，直接返回 ok
        assert data["data"]["mysql_ok"] is True
        assert data["data"]["redis_ok"] is True
