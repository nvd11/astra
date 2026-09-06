"""会话与消息管理路由单元测试."""

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


class TestConversationsRouter:
    """会话与消息路由测试类."""

    def test_create_conversation_success(self, client: TestClient, app, auth_user):
        """测试创建会话 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = Conversation(
            id="conv-1",
            user_id="user-123",
            title="测试新对话",
            model="deepseek-v4-flash",
            agent_preference="auto",
            system_prompt="system",
            is_archived=False,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )

        with patch("src.routers.conversations.ConversationRepository") as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.create.return_value = mock_conv
            mock_repo_cls.return_value = mock_repo

            response = client.post(
                "/conversations",
                json={
                    "title": "测试新对话",
                    "model": "deepseek-v4-flash",
                    "agent_preference": "auto",
                    "system_prompt": "system",
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["id"] == "conv-1"
            assert data["data"]["title"] == "测试新对话"

    def test_list_conversations_success(self, client: TestClient, app, auth_user):
        """测试获取会话列表 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = Conversation(
            id="conv-1",
            user_id="user-123",
            title="会话1",
            model="deepseek-v4-flash",
            agent_preference="auto",
            system_prompt=None,
            is_archived=False,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )

        with (
            patch("src.routers.conversations.ConversationRepository") as mock_conv_cls,
            patch("src.routers.conversations.MessageRepository") as mock_msg_cls,
        ):
            mock_conv_repo = AsyncMock()
            mock_conv_repo.list_by_user.return_value = ([mock_conv], 1)
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_message_count.return_value = 5
            mock_msg_cls.return_value = mock_msg_repo

            response = client.get("/conversations?page=1&page_size=10")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["total"] == 1
            assert len(data["data"]["items"]) == 1
            assert data["data"]["items"][0]["message_count"] == 5

    def test_get_conversation_success(self, client: TestClient, app, auth_user):
        """测试获取单个会话 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = Conversation(
            id="conv-1",
            user_id="user-123",
            title="会话1",
            model="deepseek-v4-flash",
            agent_preference="auto",
            system_prompt=None,
            is_archived=False,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )

        with (
            patch("src.routers.conversations.ConversationRepository") as mock_conv_cls,
            patch("src.routers.conversations.MessageRepository") as mock_msg_cls,
        ):
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conv
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_message_count.return_value = 3
            mock_msg_cls.return_value = mock_msg_repo

            response = client.get("/conversations/conv-1")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["id"] == "conv-1"
            assert data["data"]["message_count"] == 3

    def test_get_conversation_not_found(self, client: TestClient, app, auth_user):
        """测试获取单个会话 - 不存在或无权限."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        with patch("src.routers.conversations.ConversationRepository") as mock_conv_cls:
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = None
            mock_conv_cls.return_value = mock_conv_repo

            response = client.get("/conversations/nonexistent")
            assert response.status_code == 404

    def test_update_conversation_success(self, client: TestClient, app, auth_user):
        """测试更新会话 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = Conversation(
            id="conv-1",
            user_id="user-123",
            title="更新后的标题",
            model="deepseek-v4-flash",
            agent_preference="auto",
            system_prompt=None,
            is_archived=True,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )

        with (
            patch("src.routers.conversations.ConversationRepository") as mock_conv_cls,
            patch("src.routers.conversations.MessageRepository") as mock_msg_cls,
        ):
            mock_conv_repo = AsyncMock()
            mock_conv_repo.update.return_value = mock_conv
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_message_count.return_value = 2
            mock_msg_cls.return_value = mock_msg_repo

            response = client.put(
                "/conversations/conv-1",
                json={"title": "更新后的标题", "is_archived": True},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["title"] == "更新后的标题"
            assert data["data"]["is_archived"] is True

    def test_update_conversation_not_found(self, client: TestClient, app, auth_user):
        """测试更新会话 - 不存在."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        with patch("src.routers.conversations.ConversationRepository") as mock_conv_cls:
            mock_conv_repo = AsyncMock()
            mock_conv_repo.update.return_value = None
            mock_conv_cls.return_value = mock_conv_repo

            response = client.put(
                "/conversations/nonexistent",
                json={"title": "不存在"},
            )
            assert response.status_code == 404

    def test_delete_conversation_success(self, client: TestClient, app, auth_user):
        """测试删除会话 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = MagicMock(spec=Conversation)

        with (
            patch("src.routers.conversations.ConversationRepository") as mock_conv_cls,
            patch("src.routers.conversations.MessageRepository") as mock_msg_cls,
        ):
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conv
            mock_conv_repo.delete.return_value = True
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.delete_by_conversation.return_value = 3
            mock_msg_cls.return_value = mock_msg_repo

            response = client.delete("/conversations/conv-1")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["deleted"] is True

    def test_delete_conversation_not_found(self, client: TestClient, app, auth_user):
        """测试删除会话 - 不存在."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        with patch("src.routers.conversations.ConversationRepository") as mock_conv_cls:
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = None
            mock_conv_cls.return_value = mock_conv_repo

            response = client.delete("/conversations/nonexistent")
            assert response.status_code == 404

    def test_list_messages_success(self, client: TestClient, app, auth_user):
        """测试获取消息列表 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = MagicMock(spec=Conversation)
        mock_msg = Message(
            id="msg-1",
            conversation_id="conv-1",
            user_id="user-123",
            role="user",
            content="你好",
            message_metadata=None,
            tokens_used=10,
            is_deleted=False,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )

        with (
            patch("src.routers.conversations.ConversationRepository") as mock_conv_cls,
            patch("src.routers.conversations.MessageRepository") as mock_msg_cls,
        ):
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conv
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.list_by_conversation.return_value = ([mock_msg], 1)
            mock_msg_cls.return_value = mock_msg_repo

            response = client.get("/conversations/conv-1/messages?page=1&page_size=20")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total"] == 1
            assert data["data"]["items"][0]["content"] == "你好"

    def test_list_messages_conv_not_found(self, client: TestClient, app, auth_user):
        """测试获取消息列表 - 会话不存在."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        with patch("src.routers.conversations.ConversationRepository") as mock_conv_cls:
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = None
            mock_conv_cls.return_value = mock_conv_repo

            response = client.get("/conversations/nonexistent/messages")
            assert response.status_code == 404

    def test_edit_message_success(self, client: TestClient, app, auth_user):
        """测试修改消息 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = MagicMock(spec=Conversation)
        mock_msg = MagicMock(spec=Message)
        mock_msg.conversation_id = "conv-1"

        updated_msg = Message(
            id="msg-1",
            conversation_id="conv-1",
            user_id="user-123",
            role="user",
            content="更新后的问题",
            message_metadata=None,
            tokens_used=12,
            is_deleted=False,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )

        with (
            patch("src.routers.conversations.ConversationRepository") as mock_conv_cls,
            patch("src.routers.conversations.MessageRepository") as mock_msg_cls,
        ):
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conv
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_by_id.return_value = mock_msg
            mock_msg_repo.update_content.return_value = updated_msg
            mock_msg_cls.return_value = mock_msg_repo

            response = client.put(
                "/conversations/conv-1/messages/msg-1",
                json={"content": "更新后的问题"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["content"] == "更新后的问题"

    def test_edit_message_not_found(self, client: TestClient, app, auth_user):
        """测试修改消息 - 不存在."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = MagicMock(spec=Conversation)

        with (
            patch("src.routers.conversations.ConversationRepository") as mock_conv_cls,
            patch("src.routers.conversations.MessageRepository") as mock_msg_cls,
        ):
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conv
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_by_id.return_value = None
            mock_msg_cls.return_value = mock_msg_repo

            response = client.put(
                "/conversations/conv-1/messages/msg-nonexistent",
                json={"content": "不存在"},
            )
            assert response.status_code == 404

    def test_delete_message_success(self, client: TestClient, app, auth_user):
        """测试删除消息 - 成功."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = MagicMock(spec=Conversation)
        mock_msg = MagicMock(spec=Message)
        mock_msg.conversation_id = "conv-1"

        with (
            patch("src.routers.conversations.ConversationRepository") as mock_conv_cls,
            patch("src.routers.conversations.MessageRepository") as mock_msg_cls,
        ):
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conv
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_by_id.return_value = mock_msg
            mock_msg_repo.soft_delete.return_value = True
            mock_msg_cls.return_value = mock_msg_repo

            response = client.delete("/conversations/conv-1/messages/msg-1")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["deleted"] is True

    def test_delete_message_not_found(self, client: TestClient, app, auth_user):
        """测试删除消息 - 不存在."""
        app.dependency_overrides[get_current_user] = lambda: auth_user

        mock_conv = MagicMock(spec=Conversation)

        with (
            patch("src.routers.conversations.ConversationRepository") as mock_conv_cls,
            patch("src.routers.conversations.MessageRepository") as mock_msg_cls,
        ):
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conv
            mock_conv_cls.return_value = mock_conv_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_by_id.return_value = None
            mock_msg_cls.return_value = mock_msg_repo

            response = client.delete("/conversations/conv-1/messages/msg-nonexistent")
            assert response.status_code == 404
