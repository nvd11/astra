"""请求数据模型测试."""

import pytest
from pydantic import ValidationError

from src.models.requests import (
    CreateConversationRequest,
    EditMessageRequest,
    LoginRequest,
    LogtoCallbackRequest,
    RefreshTokenRequest,
    SendMessageRequest,
    StopChatRequest,
    UpdateConversationRequest,
    UpdatePreferenceRequest,
    UpdateProfileRequest,
)


class TestLoginRequest:
    """登录请求模型测试."""

    def test_valid_login(self):
        """测试有效登录请求."""
        req = LoginRequest(username="testuser", password="password123")
        assert req.username == "testuser"
        assert req.password == "password123"

    def test_invalid_username_empty(self):
        """测试用户名为空."""
        with pytest.raises(ValidationError):
            LoginRequest(username="", password="password123")

    def test_invalid_password_short(self):
        """测试密码过短."""
        with pytest.raises(ValidationError):
            LoginRequest(username="testuser", password="123")


class TestRefreshTokenRequest:
    """刷新令牌请求模型测试."""

    def test_valid_refresh(self):
        """测试有效刷新请求."""
        req = RefreshTokenRequest(refresh_token="valid-refresh-token")
        assert req.refresh_token == "valid-refresh-token"

    def test_invalid_refresh_empty(self):
        """测试刷新令牌为空."""
        with pytest.raises(ValidationError):
            RefreshTokenRequest(refresh_token="")


class TestLogtoCallbackRequest:
    """Logto 回调请求模型测试."""

    def test_valid_callback(self):
        """测试有效回调请求."""
        req = LogtoCallbackRequest(code="auth-code", state="random-state")
        assert req.code == "auth-code"
        assert req.state == "random-state"

    def test_invalid_code_empty(self):
        """测试授权码为空."""
        with pytest.raises(ValidationError):
            LogtoCallbackRequest(code="", state="random-state")


class TestCreateConversationRequest:
    """创建会话请求模型测试."""

    def test_valid_create(self):
        """测试有效创建请求."""
        req = CreateConversationRequest(
            title="测试会话",
            model="deepseek-v4-flash",
            agent_preference="code",
            system_prompt="You are a helpful assistant.",
        )
        assert req.title == "测试会话"
        assert req.model == "deepseek-v4-flash"
        assert req.agent_preference == "code"
        assert req.system_prompt == "You are a helpful assistant."

    def test_default_values(self):
        """测试默认值."""
        req = CreateConversationRequest()
        assert req.title == "新对话"
        assert req.model is None
        assert req.agent_preference == "auto"
        assert req.system_prompt is None


class TestUpdateConversationRequest:
    """更新会话请求模型测试."""

    def test_valid_update(self):
        """测试有效更新请求."""
        req = UpdateConversationRequest(
            title="新标题", model="gemini-3.8-flash", is_archived=True
        )
        assert req.title == "新标题"
        assert req.model == "gemini-3.8-flash"
        assert req.is_archived is True

    def test_partial_update(self):
        """测试部分更新."""
        req = UpdateConversationRequest(title="仅更新标题")
        assert req.title == "仅更新标题"
        assert req.model is None
        assert req.is_archived is None


class TestSendMessageRequest:
    """发送消息请求模型测试."""

    def test_valid_message(self):
        """测试有效消息请求."""
        req = SendMessageRequest(
            conversation_id="conv-123",
            content="你好，世界！",
            agent_override="code",
            model_override="deepseek-v4-flash",
            stream=True,
        )
        assert req.conversation_id == "conv-123"
        assert req.content == "你好，世界！"
        assert req.agent_override == "code"
        assert req.model_override == "deepseek-v4-flash"
        assert req.stream is True

    def test_content_sanitization(self):
        """测试消息内容清理."""
        req = SendMessageRequest(conversation_id="conv-123", content="  带空格的内容  ")
        assert req.content == "带空格的内容"

    def test_invalid_content_empty(self):
        """测试消息内容为空."""
        with pytest.raises(ValidationError):
            SendMessageRequest(conversation_id="conv-123", content="")

    def test_invalid_content_too_long(self):
        """测试消息内容过长."""
        with pytest.raises(ValidationError):
            SendMessageRequest(conversation_id="conv-123", content="x" * 10001)


class TestEditMessageRequest:
    """编辑消息请求模型测试."""

    def test_valid_edit(self):
        """测试有效编辑请求."""
        req = EditMessageRequest(content="编辑后的内容")
        assert req.content == "编辑后的内容"


class TestUpdateProfileRequest:
    """更新资料请求模型测试."""

    def test_valid_update(self):
        """测试有效更新请求."""
        req = UpdateProfileRequest(
            avatar_url="https://example.com/avatar.png",
            preferences={"theme": "dark", "language": "zh-CN"},
        )
        assert req.avatar_url == "https://example.com/avatar.png"
        assert req.preferences == {"theme": "dark", "language": "zh-CN"}

    def test_partial_update(self):
        """测试部分更新."""
        req = UpdateProfileRequest(avatar_url="https://example.com/new.png")
        assert req.avatar_url == "https://example.com/new.png"
        assert req.preferences is None


class TestUpdatePreferenceRequest:
    """更新偏好请求模型测试."""

    def test_valid_update(self):
        """测试有效更新请求."""
        req = UpdatePreferenceRequest(
            default_model="claude-sonnet-4-6", default_agent="creative"
        )
        assert req.default_model == "claude-sonnet-4-6"
        assert req.default_agent == "creative"


class TestStopChatRequest:
    """停止聊天请求模型测试."""

    def test_valid_stop(self):
        """测试有效停止请求."""
        req = StopChatRequest(conversation_id="conv-123")
        assert req.conversation_id == "conv-123"
