"""推理与流式对话路由测试."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.models.conversation import Conversation, Message
from src.models.user import User
from src.services.auth import get_current_user


@pytest.fixture
def auth_user():
    """测试用当前已认证用户."""
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        avatar_url=None,
        preferences={},
        default_model="deepseek-v4-flash",
        default_agent="auto",
        created_at=datetime.datetime.now(datetime.UTC),
    )


class TestChatRouter:
    """Chat 路由测试类."""

    def test_chat_stream_success(self, client: TestClient, app, auth_user):
        """测试 SSE 流式输出 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = Conversation(
            id="conv-1",
            user_id="user-123",
            title="测试对话",
            model="deepseek-v4-flash",
            agent_preference="auto",
            system_prompt="system",
            is_archived=False,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )

        mock_user_msg = Message(
            id="msg-user",
            conversation_id="conv-1",
            user_id="user-123",
            role="user",
            content="你好 Astra",
            message_metadata=None,
            tokens_used=10,
            is_deleted=False,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )

        async def mock_stream_gen(*args, **kwargs):
            yield {
                "delta": "你好",
                "finish_reason": None,
                "model": "deepseek-v4-flash",
                "agent": "direct_chat",
            }
            yield {
                "delta": "！很高兴为你服务",
                "finish_reason": "stop",
                "model": "deepseek-v4-flash",
                "agent": "direct_chat",
            }

        with (
            patch("src.routers.chat.ConversationRepository") as mock_conv_cls,
            patch("src.routers.chat.MessageRepository") as mock_msg_cls,
            patch("src.routers.chat.astream_chat", side_effect=mock_stream_gen),
            patch("src.routers.chat.get_mysql_client") as mock_mysql_factory,
        ):

            # Mock 仓储
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conv
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.create.return_value = mock_user_msg
            mock_msg_repo.get_recent_messages.return_value = [mock_user_msg]
            mock_msg_repo.list_by_conversation.return_value = ([mock_user_msg], 1)
            mock_msg_cls.return_value = mock_msg_repo

            # Mock 独立 session 保存助手回复
            mock_mysql = MagicMock()
            mock_scoped_session = AsyncMock()
            mock_mysql.session_scope.return_value.__aenter__.return_value = (
                mock_scoped_session
            )
            mock_mysql.session_scope.return_value.__aexit__.return_value = False
            mock_mysql_factory.return_value = mock_mysql

            response = client.post(
                "/chat/stream",
                headers={"X-Session-ID": "session-dev-1"},
                json={
                    "conversation_id": "conv-1",
                    "content": "你好 Astra",
                    "stream": True,
                },
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            assert mock_msg_repo.create.call_count == 2
            mock_msg_repo.create.assert_any_call(
                conversation_id="conv-1",
                user_id="user-123",
                session_id="session-dev-1",
                role="user",
                content="你好 Astra",
            )
            mock_msg_repo.create.assert_any_call(
                conversation_id="conv-1",
                user_id="user-123",
                session_id="session-dev-1",
                role="assistant",
                content="你好！很高兴为你服务",
                metadata={"agent": "direct_chat", "finish_reason": "stop"},
            )

            lines = response.text.split("\n\n")
            # 过滤空行
            non_empty_lines = [line for line in lines if line.strip()]

            # 校验包含两帧数据加 [DONE]
            assert len(non_empty_lines) >= 3
            assert "data: " in non_empty_lines[0]
            assert "你好" in non_empty_lines[0]
            assert "很高兴为你服务" in non_empty_lines[1]
            assert non_empty_lines[-1] == "data: [DONE]"

    def test_chat_stream_keepalive_ping(self, client: TestClient, app, auth_user):
        """测试 SSE 流式输出 - 慢速上游与长时间无输出时安全下发 : keepalive-ping 且无损完成."""
        import asyncio

        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = MagicMock()
        mock_conv.id = "conv-keepalive"
        mock_conv.model = "yui"
        mock_conv.agent_preference = "direct_chat"
        mock_conv.system_prompt = None

        mock_user_msg = MagicMock()
        mock_user_msg.id = "msg-user-1"
        mock_user_msg.content = "ping test"
        mock_user_msg.role = "user"
        mock_user_msg.created_at = "2026-09-17T00:00:00"
        mock_user_msg.tokens_used = 10

        async def slow_stream_gen(*args, **kwargs):
            # 第一帧内容
            yield {
                "delta": "开始任务...",
                "finish_reason": None,
                "model": "yui",
                "agent": "direct_chat",
            }
            # 模拟执行重度工具时挂起 0.1 秒
            await asyncio.sleep(0.08)
            # 最终帧内容
            yield {
                "delta": "任务完成！",
                "finish_reason": "stop",
                "model": "yui",
                "agent": "direct_chat",
            }

        from src.configs.config import get_settings

        mock_settings = MagicMock()
        mock_settings.stream_ping_interval = 0.03
        mock_settings.default_model = "yui"
        app.dependency_overrides[get_settings] = lambda: mock_settings

        with (
            patch("src.routers.chat.ConversationRepository") as mock_conv_cls,
            patch("src.routers.chat.MessageRepository") as mock_msg_cls,
            patch("src.routers.chat.astream_chat", side_effect=slow_stream_gen),
            patch("src.routers.chat.get_mysql_client") as mock_mysql_factory,
        ):
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conv
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.create.return_value = mock_user_msg
            mock_msg_repo.get_recent_messages.return_value = [mock_user_msg]
            mock_msg_repo.list_by_conversation.return_value = ([mock_user_msg], 1)
            mock_msg_cls.return_value = mock_msg_repo

            mock_mysql = MagicMock()
            mock_scoped_session = AsyncMock()
            mock_mysql.session_scope.return_value.__aenter__.return_value = (
                mock_scoped_session
            )
            mock_mysql.session_scope.return_value.__aexit__.return_value = False
            mock_mysql_factory.return_value = mock_mysql

            response = client.post(
                "/chat/stream",
                headers={"X-Session-ID": "session-dev-1"},
                json={
                    "conversation_id": "conv-keepalive",
                    "content": "执行长任务",
                    "stream": True,
                },
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            # 校验流中确实下发了 : keepalive-ping 保活注释帧
            assert ": keepalive-ping\n\n" in response.text
            # 校验即使经历了保活 ping，底层的正文和 [DONE] 也绝未被误伤或取消，完整交付
            assert "开始任务..." in response.text
            assert "任务完成！" in response.text
            assert "data: [DONE]" in response.text
            assert mock_msg_repo.create.call_count == 2

    def test_chat_stream_conversation_not_found(
        self, client: TestClient, app, auth_user
    ):
        """测试 SSE 流式输出 - 会话不存在."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        with patch("src.routers.chat.ConversationRepository") as mock_conv_cls:
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = None
            mock_conv_cls.return_value = mock_conv_repo

            response = client.post(
                "/chat/stream",
                json={
                    "conversation_id": "nonexistent",
                    "content": "hello",
                },
            )

            assert response.status_code == 404

    def test_stop_chat_success(self, client: TestClient, app, auth_user):
        """测试手动中止推理 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = MagicMock(spec=Conversation)
        mock_conv.id = "conv-1"

        with (
            patch("src.routers.chat.ConversationRepository") as mock_conv_cls,
            patch("src.routers.chat.get_redis_client") as mock_get_redis,
        ):

            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conv
            mock_conv_cls.return_value = mock_conv_repo

            mock_redis = AsyncMock()
            mock_redis.setex = AsyncMock()
            mock_get_redis.return_value = mock_redis

            response = client.post("/chat/stop", json={"conversation_id": "conv-1"})

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["stopped"] is True
            mock_redis.setex.assert_called_once_with("chat:stop:conv-1", 60, "1")

    def test_stop_chat_conversation_not_found(self, client: TestClient, app, auth_user):
        """测试手动中止推理 - 会话不存在."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        with patch("src.routers.chat.ConversationRepository") as mock_conv_cls:
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = None
            mock_conv_cls.return_value = mock_conv_repo

            response = client.post(
                "/chat/stop", json={"conversation_id": "nonexistent"}
            )
            assert response.status_code == 404

    def test_list_models_cached(self, client: TestClient, app):
        """测试获取模型列表 - Redis 缓存命中."""
        import json

        from src.engine.redis_client import get_redis_client

        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(
            [
                {
                    "id": "gemini-3.8-flash",
                    "name": "Gemini 3.8 Flash",
                    "provider": "Google",
                }
            ]
        )
        app.dependency_overrides[get_redis_client] = lambda: mock_redis

        response = client.get("/chat/models")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Gemini 3.8 Flash"

    def test_list_models_from_gateway(self, client: TestClient, app):
        """测试获取模型列表 - 穿透查询网关并写入缓存."""
        from src.engine.redis_client import get_redis_client

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()
        app.dependency_overrides[get_redis_client] = lambda: mock_redis

        mock_litellm = AsyncMock()
        mock_litellm.get_models.return_value = [
            {"id": "gemini-3.8-flash"},
            {"id": "kimi-k3"},
            {"id": "gpt-5.6-luna-a6"},
        ]

        with patch("src.routers.chat.get_litellm_client", return_value=mock_litellm):
            response = client.get("/chat/models")
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert len(data["data"]) == 3
            assert data["data"][0]["provider"] == "Google"
            assert data["data"][1]["provider"] == "Moonshot"
            assert data["data"][2]["provider"] == "OpenAI"
            mock_redis.setex.assert_called_once()

    def test_list_agents(self, client: TestClient, app):
        """测试获取支持的智能体列表."""
        response = client.get("/chat/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        agents = data["data"]
        assert len(agents) >= 4
        ids = [a["id"] for a in agents]
        assert "auto" in ids
        assert "code_assistant" in ids
        assert "deep_reasoner" in ids
        assert "direct_chat" in ids
