"""会话与消息仓储层单元测试."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import (
    Conversation,
    ConversationRepository,
    Message,
    MessageRepository,
)


class TestConversationRepository:
    """会话数据仓库测试类."""

    @pytest.fixture
    def mock_session(self):
        """Mock 数据库会话."""
        session = AsyncMock(spec=AsyncSession)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """会话仓储实例."""
        return ConversationRepository(mock_session)

    @pytest.mark.asyncio
    async def test_create_conversation(self, repo, mock_session):
        """测试创建会话."""
        conv = await repo.create(
            user_id="user-123",
            title="测试对话",
            model="deepseek-v4-flash",
            agent_preference="auto",
            system_prompt="You are helpful",
            session_id="session-device-1",
        )
        assert conv.user_id == "user-123"
        assert conv.session_id == "session-device-1"
        assert conv.title == "测试对话"
        assert conv.model == "deepseek-v4-flash"
        assert conv.agent_preference == "auto"
        assert conv.system_prompt == "You are helpful"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repo, mock_session):
        """测试获取会话 - 成功."""
        mock_conv = MagicMock(spec=Conversation)
        mock_conv.id = "conv-1"
        mock_conv.user_id = "user-123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conv
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_id("conv-1", "user-123")
        assert result is mock_conv

    @pytest.mark.asyncio
    async def test_get_by_id_not_found_or_different_user(self, repo, mock_session):
        """测试获取会话 - 行级隔离不存在或跨用户."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_id("conv-1", "user-other")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_by_user(self, repo, mock_session):
        """测试分页列出用户会话."""
        # 第一次 execute 返回 count
        mock_count_res = MagicMock()
        mock_count_res.scalar_one.return_value = 2

        # 第二次 execute 返回 items
        mock_items_res = MagicMock()
        conv1 = MagicMock(spec=Conversation)
        conv2 = MagicMock(spec=Conversation)
        mock_items_res.scalars.return_value.all.return_value = [conv1, conv2]

        mock_session.execute.side_effect = [mock_count_res, mock_items_res]

        items, total = await repo.list_by_user(
            "user-123", page=1, page_size=10, is_archived=False
        )
        assert total == 2
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_update_conversation_success(self, repo, mock_session):
        """测试更新会话 - 成功."""
        mock_conv = MagicMock(spec=Conversation)
        mock_conv.id = "conv-1"
        mock_conv.user_id = "user-123"
        mock_conv.title = "旧标题"

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(repo, "get_by_id", AsyncMock(return_value=mock_conv))
            updated = await repo.update(
                "conv-1", "user-123", title="新标题", is_archived=True
            )
            assert updated is mock_conv
            assert mock_conv.title == "新标题"
            assert mock_conv.is_archived is True

    @pytest.mark.asyncio
    async def test_update_conversation_not_found(self, repo):
        """测试更新会话 - 未找到."""
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(repo, "get_by_id", AsyncMock(return_value=None))
            updated = await repo.update("nonexistent", "user-123", title="新标题")
            assert updated is None

    @pytest.mark.asyncio
    async def test_delete_conversation_success(self, repo, mock_session):
        """测试删除会话 - 成功."""
        mock_conv = MagicMock(spec=Conversation)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(repo, "get_by_id", AsyncMock(return_value=mock_conv))
            success = await repo.delete("conv-1", "user-123")
            assert success is True
            mock_session.delete.assert_called_once_with(mock_conv)

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, repo, mock_session):
        """测试删除会话 - 不存在."""
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(repo, "get_by_id", AsyncMock(return_value=None))
            success = await repo.delete("conv-1", "user-123")
            assert success is False
            mock_session.delete.assert_not_called()


class TestMessageRepository:
    """消息数据仓库测试类."""

    @pytest.fixture
    def mock_session(self):
        """Mock 数据库会话."""
        session = AsyncMock(spec=AsyncSession)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """消息仓储实例."""
        return MessageRepository(mock_session)

    @pytest.mark.asyncio
    async def test_create_message(self, repo, mock_session):
        """测试创建消息."""
        msg = await repo.create(
            conversation_id="conv-1",
            user_id="user-123",
            role="user",
            content="你好",
            metadata={"step": 1},
            tokens_used=15,
            session_id="session-device-1",
        )
        assert msg.conversation_id == "conv-1"
        assert msg.user_id == "user-123"
        assert msg.session_id == "session-device-1"
        assert msg.role == "user"
        assert msg.content == "你好"
        assert msg.tokens_used == 15
        assert msg.message_metadata == {"step": 1}
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id(self, repo, mock_session):
        """测试查询单条消息."""
        mock_msg = MagicMock(spec=Message)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_msg
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_id("msg-1", "user-123")
        assert result is mock_msg

    @pytest.mark.asyncio
    async def test_list_by_conversation(self, repo, mock_session):
        """测试分页获取消息列表."""
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 5

        mock_items = MagicMock()
        mock_items.scalars.return_value.all.return_value = [MagicMock(spec=Message)]

        mock_session.execute.side_effect = [mock_count, mock_items]

        items, total = await repo.list_by_conversation(
            "conv-1", "user-123", page=1, page_size=20
        )
        assert total == 5
        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_get_recent_messages(self, repo, mock_session):
        """测试倒序拉取最新 N 条消息并反转为时间升序."""
        msg_earlier = MagicMock(spec=Message, id="msg-1", content="First")
        msg_later = MagicMock(spec=Message, id="msg-2", content="Second")

        mock_items = MagicMock()
        # 数据库 ORDER BY created_at DESC 先查出最新的 msg_later，再查出 msg_earlier
        mock_items.scalars.return_value.all.return_value = [msg_later, msg_earlier]
        mock_session.execute.return_value = mock_items

        items = await repo.get_recent_messages("conv-1", "user-123", limit=20)
        # 返回列表应被 reversed 为时间升序 [msg_earlier, msg_later]
        assert len(items) == 2
        assert items[0] is msg_earlier
        assert items[1] is msg_later

    @pytest.mark.asyncio
    async def test_get_message_count(self, repo, mock_session):
        """测试获取消息数量."""
        mock_res = MagicMock()
        mock_res.scalar_one.return_value = 42
        mock_session.execute.return_value = mock_res

        count = await repo.get_message_count("conv-1", "user-123")
        assert count == 42

    @pytest.mark.asyncio
    async def test_get_message_counts_by_conversations(self, repo, mock_session):
        """测试批量获取会话消息数量 (防 N+1)."""
        # 空列表直接返回空字典
        empty_res = await repo.get_message_counts_by_conversations([], "user-123")
        assert empty_res == {}

        mock_res = MagicMock()
        mock_res.tuples.return_value.all.return_value = [
            ("conv-1", 10),
            ("conv-2", 20),
        ]
        mock_session.execute.return_value = mock_res

        res = await repo.get_message_counts_by_conversations(
            ["conv-1", "conv-2"], "user-123"
        )
        assert res == {"conv-1": 10, "conv-2": 20}

    @pytest.mark.asyncio
    async def test_update_content_success(self, repo, mock_session):
        """测试更新消息内容 - 成功."""
        mock_msg = MagicMock(spec=Message)
        mock_msg.content = "旧内容"
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(repo, "get_by_id", AsyncMock(return_value=mock_msg))
            updated = await repo.update_content("msg-1", "user-123", "新内容")
            assert updated is mock_msg
            assert mock_msg.content == "新内容"

    @pytest.mark.asyncio
    async def test_update_content_not_found(self, repo):
        """测试更新消息内容 - 未找到."""
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(repo, "get_by_id", AsyncMock(return_value=None))
            updated = await repo.update_content("msg-1", "user-123", "新内容")
            assert updated is None

    @pytest.mark.asyncio
    async def test_soft_delete_success(self, repo, mock_session):
        """测试软删除消息 - 成功."""
        mock_msg = MagicMock(spec=Message)
        mock_msg.is_deleted = False
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(repo, "get_by_id", AsyncMock(return_value=mock_msg))
            ok = await repo.soft_delete("msg-1", "user-123")
            assert ok is True
            assert mock_msg.is_deleted is True

    @pytest.mark.asyncio
    async def test_soft_delete_not_found(self, repo):
        """测试软删除消息 - 未找到."""
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(repo, "get_by_id", AsyncMock(return_value=None))
            ok = await repo.soft_delete("msg-1", "user-123")
            assert ok is False

    @pytest.mark.asyncio
    async def test_delete_by_conversation(self, repo, mock_session):
        """测试按会话批量删除消息."""
        msg1 = MagicMock(spec=Message)
        msg2 = MagicMock(spec=Message)
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = [msg1, msg2]
        mock_session.execute.return_value = mock_res

        count = await repo.delete_by_conversation("conv-1", "user-123")
        assert count == 2
        assert msg1.is_deleted is True
        assert msg2.is_deleted is True
