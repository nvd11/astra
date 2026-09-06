"""响应数据模型测试."""

from datetime import datetime

from src.models.responses import (
    BaseResponse,
    ChatStreamChunkData,
    ConversationData,
    ConversationResponse,
    HealthResponse,
    HealthResponseData,
    MessageData,
    MessageResponse,
    PaginatedData,
    SessionListResponse,
    TokenResponse,
    TokenResponseData,
    UsageStatsData,
    UsageStatsResponse,
    UserInfoData,
    UserSessionItem,
)


class TestBaseResponse:
    """基础响应模型测试."""

    def test_default_values(self):
        """测试默认值."""
        resp = BaseResponse()
        assert resp.code == 0
        assert resp.message == "success"
        assert resp.data is None
        assert isinstance(resp.timestamp, datetime)

    def test_with_data(self):
        """测试带数据响应."""
        resp = BaseResponse(data={"key": "value"})
        assert resp.data == {"key": "value"}

    def test_generic_type(self):
        """测试泛型类型."""
        resp = BaseResponse[str](data="test")
        assert resp.data == "test"


class TestPaginatedData:
    """分页数据模型测试."""

    def test_valid_pagination(self):
        """测试有效分页数据."""
        data = PaginatedData[str](
            items=["a", "b", "c"], total=10, page=1, page_size=3, has_more=True
        )
        assert data.items == ["a", "b", "c"]
        assert data.total == 10
        assert data.page == 1
        assert data.page_size == 3
        assert data.has_more is True


class TestHealthResponseData:
    """健康检查响应数据模型测试."""

    def test_valid_health(self):
        """测试有效健康数据."""
        data = HealthResponseData(
            status="ok",
            service="Astra",
            version="1.0.0",
            mysql_ok=True,
            redis_ok=True,
            uptime_seconds=123.45,
        )
        assert data.status == "ok"
        assert data.service == "Astra"
        assert data.version == "1.0.0"
        assert data.mysql_ok is True
        assert data.redis_ok is True
        assert data.uptime_seconds == 123.45


class TestUserInfoData:
    """用户信息数据模型测试."""

    def test_valid_user(self):
        """测试有效用户数据."""
        now = datetime.utcnow()
        data = UserInfoData(
            id="user-123",
            username="testuser",
            email="test@example.com",
            avatar_url="https://example.com/avatar.png",
            preferences={"theme": "dark"},
            default_model="deepseek-v4-flash",
            default_agent="auto",
            created_at=now,
        )
        assert data.id == "user-123"
        assert data.username == "testuser"
        assert data.email == "test@example.com"
        assert data.avatar_url == "https://example.com/avatar.png"
        assert data.preferences == {"theme": "dark"}
        assert data.default_model == "deepseek-v4-flash"
        assert data.default_agent == "auto"
        assert data.created_at == now


class TestTokenResponseData:
    """令牌响应数据模型测试."""

    def test_valid_token(self):
        """测试有效令牌数据."""
        user = UserInfoData(
            id="user-123", username="testuser", created_at=datetime.utcnow()
        )
        data = TokenResponseData(
            access_token="access-token",
            refresh_token="refresh-token",
            expires_in=7200,
            user=user,
        )
        assert data.access_token == "access-token"
        assert data.refresh_token == "refresh-token"
        assert data.token_type == "Bearer"
        assert data.expires_in == 7200
        assert data.user.id == "user-123"


class TestConversationData:
    """会话数据模型测试."""

    def test_valid_conversation(self):
        """测试有效会话数据."""
        now = datetime.utcnow()
        data = ConversationData(
            id="conv-123",
            title="测试会话",
            model="deepseek-v4-flash",
            agent_preference="auto",
            system_prompt="You are helpful",
            is_archived=False,
            created_at=now,
            updated_at=now,
            message_count=5,
        )
        assert data.id == "conv-123"
        assert data.title == "测试会话"
        assert data.model == "deepseek-v4-flash"
        assert data.agent_preference == "auto"
        assert data.system_prompt == "You are helpful"
        assert data.is_archived is False
        assert data.message_count == 5


class TestMessageData:
    """消息数据模型测试."""

    def test_valid_message(self):
        """测试有效消息数据."""
        now = datetime.utcnow()
        data = MessageData(
            id="msg-123",
            conversation_id="conv-123",
            role="user",
            content="你好",
            metadata={"key": "value"},
            tokens_used=10,
            created_at=now,
        )
        assert data.id == "msg-123"
        assert data.conversation_id == "conv-123"
        assert data.role == "user"
        assert data.content == "你好"
        assert data.metadata == {"key": "value"}
        assert data.tokens_used == 10


class TestUserSessionItem:
    """用户会话条目模型测试."""

    def test_valid_session(self):
        """测试有效会话条目."""
        now = datetime.utcnow()
        data = UserSessionItem(
            id="session-123",
            device_info="Chrome on Windows",
            ip_address="192.168.1.1",
            last_active_at=now,
            expires_at=now,
            is_current=True,
        )
        assert data.id == "session-123"
        assert data.device_info == "Chrome on Windows"
        assert data.ip_address == "192.168.1.1"
        assert data.is_current is True


class TestUsageStatsData:
    """用量统计数据模型测试."""

    def test_valid_stats(self):
        """测试有效用量数据."""
        data = UsageStatsData(
            total_messages=100,
            total_tokens=50000,
            total_conversations=10,
            today_messages=5,
            today_tokens=2500,
        )
        assert data.total_messages == 100
        assert data.total_tokens == 50000
        assert data.total_conversations == 10
        assert data.today_messages == 5
        assert data.today_tokens == 2500


class TestChatStreamChunkData:
    """流式输出数据模型测试."""

    def test_valid_chunk(self):
        """测试有效流式数据."""
        data = ChatStreamChunkData(
            id="chunk-123",
            delta="Hello",
            finish_reason=None,
            model="deepseek-v4-flash",
            agent="general",
        )
        assert data.id == "chunk-123"
        assert data.delta == "Hello"
        assert data.finish_reason is None
        assert data.model == "deepseek-v4-flash"
        assert data.agent == "general"


class TestResponseAliases:
    """响应类型别名测试."""

    def test_health_response(self):
        """测试健康响应别名."""
        resp = HealthResponse(
            data=HealthResponseData(
                status="ok",
                service="Astra",
                version="1.0.0",
                mysql_ok=True,
                redis_ok=True,
            )
        )
        assert resp.code == 0
        assert resp.data.status == "ok"

    def test_token_response(self):
        """测试令牌响应别名."""
        user = UserInfoData(id="u1", username="test", created_at=datetime.utcnow())
        resp = TokenResponse(
            data=TokenResponseData(
                access_token="at", refresh_token="rt", expires_in=7200, user=user
            )
        )
        assert resp.data.access_token == "at"

    def test_conversation_response(self):
        """测试会话响应别名."""
        now = datetime.utcnow()
        conv = ConversationData(
            id="c1",
            title="Test",
            model="m",
            agent_preference="a",
            created_at=now,
            updated_at=now,
        )
        resp = ConversationResponse(data=conv)
        assert resp.data.id == "c1"

    def test_message_response(self):
        """测试消息响应别名."""
        msg = MessageData(
            id="m1",
            conversation_id="c1",
            role="user",
            content="hi",
            created_at=datetime.utcnow(),
        )
        resp = MessageResponse(data=msg)
        assert resp.data.id == "m1"

    def test_session_list_response(self):
        """测试会话列表响应别名."""
        now = datetime.utcnow()
        session = UserSessionItem(
            id="s1",
            device_info="Chrome",
            ip_address="127.0.0.1",
            last_active_at=now,
            expires_at=now,
            is_current=True,
        )
        resp = SessionListResponse(data=[session])
        assert len(resp.data) == 1
        assert resp.data[0].id == "s1"

    def test_usage_stats_response(self):
        """测试用量统计响应别名."""
        stats = UsageStatsData(
            total_messages=1,
            total_tokens=10,
            total_conversations=1,
            today_messages=1,
            today_tokens=10,
        )
        resp = UsageStatsResponse(data=stats)
        assert resp.data.total_messages == 1
