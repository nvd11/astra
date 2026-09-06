"""API 请求数据模型定义."""

from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """基础账密登录请求."""

    username: Annotated[str, Field(min_length=1, max_length=64, description="用户名")]
    password: Annotated[str, Field(min_length=6, max_length=128, description="密码")]


class RefreshTokenRequest(BaseModel):
    """刷新 Access Token 请求."""

    refresh_token: Annotated[str, Field(min_length=1, description="Refresh Token")]


class LogtoCallbackRequest(BaseModel):
    """Logto SSO 回调请求."""

    code: Annotated[str, Field(min_length=1, description="授权码")]
    state: Annotated[str, Field(min_length=1, description="状态参数")]


class CreateConversationRequest(BaseModel):
    """创建会话请求."""

    title: Annotated[str | None, Field(max_length=255, description="会话标题")] = (
        "新对话"
    )
    model: Annotated[str | None, Field(max_length=64, description="绑定模型")] = None
    agent_preference: Annotated[str, Field(max_length=64, description="绑定 Agent")] = (
        "auto"
    )
    system_prompt: Annotated[str | None, Field(description="自定义系统提示词")] = None


class UpdateConversationRequest(BaseModel):
    """修改会话请求."""

    title: Annotated[str | None, Field(max_length=255, description="会话标题")] = None
    model: Annotated[str | None, Field(max_length=64, description="绑定模型")] = None
    agent_preference: Annotated[
        str | None, Field(max_length=64, description="绑定 Agent")
    ] = None
    system_prompt: Annotated[str | None, Field(description="自定义系统提示词")] = None
    is_archived: Annotated[bool | None, Field(description="是否归档")] = None


class SendMessageRequest(BaseModel):
    """发送对话消息请求."""

    conversation_id: Annotated[
        str, Field(min_length=1, max_length=36, description="会话 ID")
    ]
    content: Annotated[
        str, Field(min_length=1, max_length=10000, description="消息正文")
    ]
    agent_override: Annotated[
        str | None, Field(max_length=64, description="强制指定 Agent")
    ] = None
    model_override: Annotated[
        str | None, Field(max_length=64, description="强制指定模型")
    ] = None
    stream: Annotated[bool, Field(description="是否流式输出")] = True

    @field_validator("content", mode="before")
    @classmethod
    def sanitize_content(cls, v: Any) -> Any:
        """清理消息内容."""
        if isinstance(v, str):
            return v.strip()
        return v


class EditMessageRequest(BaseModel):
    """编辑消息请求."""

    content: Annotated[
        str, Field(min_length=1, max_length=10000, description="新消息正文")
    ]


class UpdateProfileRequest(BaseModel):
    """修改个人资料请求."""

    avatar_url: Annotated[str | None, Field(max_length=500, description="头像 URL")] = (
        None
    )
    preferences: Annotated[dict[str, Any] | None, Field(description="用户偏好设置")] = (
        None
    )


class UpdatePreferenceRequest(BaseModel):
    """修改用户偏好请求."""

    default_model: Annotated[
        str | None, Field(max_length=64, description="默认模型")
    ] = None
    default_agent: Annotated[
        str | None, Field(max_length=64, description="默认 Agent")
    ] = None


class StopChatRequest(BaseModel):
    """手动中止推理请求."""

    conversation_id: Annotated[
        str, Field(min_length=1, max_length=36, description="会话 ID")
    ]
