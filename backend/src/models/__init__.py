"""数据模型模块初始化."""

from .conversation import (
    Conversation,
    ConversationRepository,
    Message,
    MessageRepository,
)
from .knowledge import DocumentChunk, KnowledgeDocument
from .user import Base, SessionRepository, User, UserRepository, UserSession

__all__ = [
    "Base",
    "User",
    "UserSession",
    "UserRepository",
    "SessionRepository",
    "Conversation",
    "Message",
    "ConversationRepository",
    "MessageRepository",
    "KnowledgeDocument",
    "DocumentChunk",
]

from .requests import (
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
from .responses import (
    BaseResponse,
    ChatStreamChunkData,
    ConversationData,
    ConversationListResponse,
    ConversationResponse,
    HealthResponse,
    HealthResponseData,
    MessageData,
    MessageListResponse,
    MessageResponse,
    PaginatedData,
    SessionListResponse,
    TokenResponse,
    TokenResponseData,
    UsageStatsData,
    UsageStatsResponse,
    UserInfoData,
    UserInfoResponse,
    UserSessionItem,
)

__all__ = [
    # 请求模型
    "LoginRequest",
    "RefreshTokenRequest",
    "LogtoCallbackRequest",
    "CreateConversationRequest",
    "UpdateConversationRequest",
    "SendMessageRequest",
    "EditMessageRequest",
    "UpdateProfileRequest",
    "UpdatePreferenceRequest",
    "StopChatRequest",
    # 响应模型
    "BaseResponse",
    "PaginatedData",
    "HealthResponseData",
    "HealthResponse",
    "UserInfoData",
    "TokenResponseData",
    "TokenResponse",
    "UserInfoResponse",
    "ConversationData",
    "ConversationResponse",
    "ConversationListResponse",
    "MessageData",
    "MessageResponse",
    "MessageListResponse",
    "UserSessionItem",
    "SessionListResponse",
    "UsageStatsData",
    "UsageStatsResponse",
    "ChatStreamChunkData",
]
