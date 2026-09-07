"""API 响应数据模型定义."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """系统级统一通用响应外壳."""

    code: int = Field(default=0, description="业务状态码, 0 表示成功")
    message: str = Field(default="success", description="响应消息")
    data: T | None = Field(default=None, description="业务数据载荷")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedData(BaseModel, Generic[T]):
    """通用分页数据包装器."""

    items: list[T] = Field(description="当前页数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    has_more: bool = Field(description="是否有更多数据")


class HealthResponseData(BaseModel):
    """探针健康状态明细."""

    status: str = Field(description="服务状态 (ok/error)")
    service: str = Field(description="服务名称")
    version: str = Field(description="服务版本")
    mysql_ok: bool = Field(description="MySQL 是否连通")
    redis_ok: bool = Field(description="Redis 是否连通")
    uptime_seconds: float | None = Field(default=None, description="运行时长 (秒)")


class UserInfoData(BaseModel):
    """用户核心资料实体."""

    id: str = Field(description="用户唯一 ID")
    username: str = Field(description="用户名")
    email: str | None = Field(default=None, description="邮箱")
    avatar_url: str | None = Field(default=None, description="头像 URL")
    preferences: dict[str, Any] = Field(
        default_factory=dict, description="用户偏好设置"
    )
    default_model: str = Field(default="deepseek-v4-flash", description="默认模型")
    default_agent: str = Field(default="auto", description="默认 Agent")
    created_at: datetime = Field(description="创建时间")


class TokenResponseData(BaseModel):
    """登录成功后签发的令牌与用户数据."""

    access_token: str = Field(description="Access Token")
    refresh_token: str = Field(description="Refresh Token")
    token_type: str = Field(default="Bearer", description="Token 类型")
    expires_in: int = Field(description="过期时间 (秒)")
    user: UserInfoData = Field(description="当前登录用户信息")


class ConversationData(BaseModel):
    """单个会话元数据."""

    id: str = Field(description="会话 ID")
    session_id: str | None = Field(default=None, description="发起创建的设备会话 ID")
    title: str = Field(description="会话标题")
    model: str = Field(description="绑定模型")
    agent_preference: str = Field(description="绑定 Agent")
    system_prompt: str | None = Field(default=None, description="自定义系统提示词")
    is_archived: bool = Field(default=False, description="是否已归档")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    message_count: int | None = Field(default=None, description="消息总数")


class MessageData(BaseModel):
    """消息明细实体."""

    id: str = Field(description="消息 ID")
    conversation_id: str = Field(description="所属会话 ID")
    session_id: str | None = Field(default=None, description="发送该消息的设备会话 ID")
    role: str = Field(description="角色 (user/assistant/system/tool)")
    content: str = Field(description="消息正文")
    metadata: dict[str, Any] | None = Field(default=None, description="元数据")
    tokens_used: int | None = Field(default=None, description="消耗 Token 数")
    created_at: datetime = Field(description="创建时间")


class UserSessionItem(BaseModel):
    """活跃设备会话条目."""

    id: str = Field(description="会话记录 ID")
    device_info: str = Field(description="设备信息")
    ip_address: str = Field(description="登录 IP")
    last_active_at: datetime = Field(description="最后活跃时间")
    expires_at: datetime = Field(description="过期时间")
    is_current: bool = Field(description="是否为当前设备")


class UsageStatsData(BaseModel):
    """用户用量统计."""

    total_messages: int = Field(description="累计消息数")
    total_tokens: int = Field(description="累计消耗 Token")
    total_conversations: int = Field(description="累计会话数")
    today_messages: int = Field(description="今日消息数")
    today_tokens: int = Field(description="今日消耗 Token")


class ChatStreamChunkData(BaseModel):
    """SSE 流式输出单帧数据载荷."""

    id: str = Field(description="消息 ID")
    delta: str = Field(description="增量内容")
    finish_reason: str | None = Field(default=None, description="结束原因")
    model: str = Field(description="模型名称")
    agent: str = Field(description="Agent 名称")


# 常用类型别名
HealthResponse = BaseResponse[HealthResponseData]
TokenResponse = BaseResponse[TokenResponseData]
UserInfoResponse = BaseResponse[UserInfoData]
ConversationResponse = BaseResponse[ConversationData]
ConversationListResponse = BaseResponse[PaginatedData[ConversationData]]
MessageResponse = BaseResponse[MessageData]
MessageListResponse = BaseResponse[PaginatedData[MessageData]]
SessionListResponse = BaseResponse[list[UserSessionItem]]
UsageStatsResponse = BaseResponse[UsageStatsData]
