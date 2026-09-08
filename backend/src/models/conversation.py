"""会话与消息 ORM 模型及仓储层.

支持基于用户 ID (user_id) 的严格行级隔离.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from src.models.user import Base, UserSession


class Conversation(Base):
    """会话表 ORM 模型."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("user_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="新对话")
    model: Mapped[str] = mapped_column(
        String(64), nullable=False, default="deepseek-v4-flash"
    )
    agent_preference: Mapped[str] = mapped_column(
        String(64), nullable=False, default="auto"
    )
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        index=True,
    )


class Message(Base):
    """消息表 ORM 模型."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("user_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user | assistant | system | tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    tokens_used: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class ConversationRepository:
    """会话数据仓库，支持严格基于 user_id 的多租户行级隔离."""

    def __init__(self, session: AsyncSession) -> None:
        """初始化仓储.

        Args:
            session: 异步数据库会话
        """
        self.session = session

    async def create(
        self,
        user_id: str,
        title: str = "新对话",
        model: str = "deepseek-v4-flash",
        agent_preference: str = "auto",
        system_prompt: str | None = None,
        session_id: str | None = None,
    ) -> Conversation:
        """创建新会话.

        Args:
            user_id: 所属用户 ID
            title: 会话标题
            model: 模型名称
            agent_preference: Agent 偏好
            system_prompt: 系统提示词
            session_id: 发起创建的设备会话 ID (可选审计溯源)

        Returns:
            Conversation: 创建的会话实体
        """
        valid_session_id = None
        if session_id:
            res = await self.session.execute(
                select(UserSession.id).where(UserSession.id == session_id)
            )
            if res.scalar_one_or_none():
                valid_session_id = session_id

        conversation = Conversation(
            user_id=user_id,
            session_id=valid_session_id,
            title=title,
            model=model,
            agent_preference=agent_preference,
            system_prompt=system_prompt,
        )
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def get_by_id(
        self, conversation_id: str, user_id: str
    ) -> Conversation | None:
        """根据 ID 和 user_id 获取会话（强制行级隔离）.

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID

        Returns:
            Conversation | None: 会话实体或 None
        """
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        is_archived: bool | None = False,
    ) -> tuple[list[Conversation], int]:
        """分页获取用户的会话列表.

        Args:
            user_id: 用户 ID
            page: 页码 (1-based)
            page_size: 每页数量
            is_archived: 归档过滤状态 (None 则不限制)

        Returns:
            tuple[list[Conversation], int]: (会话列表, 总数)
        """
        query = select(Conversation).where(Conversation.user_id == user_id)
        count_query = (
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.user_id == user_id)
        )

        if is_archived is not None:
            query = query.where(Conversation.is_archived == is_archived)
            count_query = count_query.where(Conversation.is_archived == is_archived)

        # 统计总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one() or 0

        # 分页查询，按更新时间倒序
        offset = (page - 1) * page_size
        query = (
            query.order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update(
        self,
        conversation_id: str,
        user_id: str,
        **kwargs: Any,
    ) -> Conversation | None:
        """更新会话.

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID (行级隔离)
            **kwargs: 要更新的属性

        Returns:
            Conversation | None: 更新后的会话或 None
        """
        conversation = await self.get_by_id(conversation_id, user_id)
        if not conversation:
            return None

        for key, value in kwargs.items():
            if hasattr(conversation, key) and value is not None:
                setattr(conversation, key, value)

        conversation.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def delete(self, conversation_id: str, user_id: str) -> bool:
        """删除会话及其所有关联消息.

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID

        Returns:
            bool: 是否删除成功
        """
        conversation = await self.get_by_id(conversation_id, user_id)
        if not conversation:
            return False

        # 删除会话
        await self.session.delete(conversation)
        await self.session.flush()
        return True


class MessageRepository:
    """消息数据仓库，支持严格基于 user_id 和 conversation_id 的隔离."""

    def __init__(self, session: AsyncSession) -> None:
        """初始化仓储.

        Args:
            session: 异步数据库会话
        """
        self.session = session

    async def create(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        tokens_used: int | None = None,
        session_id: str | None = None,
    ) -> Message:
        """创建一条新消息.

        Args:
            conversation_id: 所属会话 ID
            user_id: 用户 ID
            role: 消息角色
            content: 消息内容
            metadata: 元数据 (Token 明细、推理步骤等)
            tokens_used: 消耗 Token 数
            session_id: 登录设备会话 ID (可选审计溯源)

        Returns:
            Message: 创建的消息实体
        """
        valid_session_id = None
        if session_id:
            res = await self.session.execute(
                select(UserSession.id).where(UserSession.id == session_id)
            )
            if res.scalar_one_or_none():
                valid_session_id = session_id

        msg = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            session_id=valid_session_id,
            role=role,
            content=content,
            message_metadata=metadata,
            tokens_used=tokens_used,
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg

    async def get_by_id(self, message_id: str, user_id: str) -> Message | None:
        """获取指定单条消息（行级隔离）.

        Args:
            message_id: 消息 ID
            user_id: 用户 ID

        Returns:
            Message | None: 消息实体或 None
        """
        stmt = select(Message).where(
            Message.id == message_id,
            Message.user_id == user_id,
            Message.is_deleted == False,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_conversation(
        self,
        conversation_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Message], int]:
        """分页获取会话的历史消息列表.

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID
            page: 页码 (1-based)
            page_size: 每页数量

        Returns:
            tuple[list[Message], int]: (消息列表按时间升序, 总数)
        """
        count_stmt = (
            select(func.count())
            .select_from(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.user_id == user_id,
                Message.is_deleted == False,  # noqa: E712
            )
        )
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.user_id == user_id,
                Message.is_deleted == False,  # noqa: E712
            )
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_recent_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 20,
    ) -> list[Message]:
        """获取会话最近的 N 条消息 (按时间升序返回).

        倒序查询最新的 limit 条记录，然后按时间正序排列返回，供 LLM 多轮上下文构建使用.

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID
            limit: 最大拉取消息数量

        Returns:
            list[Message]: 最近 N 条按时间升序排列的消息列表
        """
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.user_id == user_id,
                Message.is_deleted == False,  # noqa: E712
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        return list(reversed(items))

    async def get_message_count(self, conversation_id: str, user_id: str) -> int:
        """获取会话内未删除消息总数.

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID

        Returns:
            int: 消息总数
        """
        stmt = (
            select(func.count())
            .select_from(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.user_id == user_id,
                Message.is_deleted == False,  # noqa: E712
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def get_message_counts_by_conversations(
        self,
        conversation_ids: list[str],
        user_id: str,
    ) -> dict[str, int]:
        """批量获取多个会话各自的未删除消息总数 (消除 N+1 查询).

        Args:
            conversation_ids: 会话 ID 列表
            user_id: 用户 ID

        Returns:
            dict[str, int]: 会话 ID 到消息数的映射字典
        """
        if not conversation_ids:
            return {}

        stmt = (
            select(Message.conversation_id, func.count(Message.id))
            .where(
                Message.conversation_id.in_(conversation_ids),
                Message.user_id == user_id,
                Message.is_deleted == False,  # noqa: E712
            )
            .group_by(Message.conversation_id)
        )
        result = await self.session.execute(stmt)
        return dict(result.tuples().all())

    async def update_content(
        self,
        message_id: str,
        user_id: str,
        new_content: str,
    ) -> Message | None:
        """编辑消息内容.

        Args:
            message_id: 消息 ID
            user_id: 用户 ID
            new_content: 新内容

        Returns:
            Message | None: 更新后的消息或 None
        """
        msg = await self.get_by_id(message_id, user_id)
        if not msg:
            return None

        msg.content = new_content
        msg.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg

    async def soft_delete(self, message_id: str, user_id: str) -> bool:
        """软删除单条消息.

        Args:
            message_id: 消息 ID
            user_id: 用户 ID

        Returns:
            bool: 是否删除成功
        """
        msg = await self.get_by_id(message_id, user_id)
        if not msg:
            return False

        msg.is_deleted = True
        msg.updated_at = datetime.now(UTC)
        await self.session.flush()
        return True

    async def delete_by_conversation(self, conversation_id: str, user_id: str) -> int:
        """软删除指定会话的所有消息.

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID

        Returns:
            int: 标记删除的消息数量
        """
        stmt = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.user_id == user_id,
            Message.is_deleted == False,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        msgs = list(result.scalars().all())

        for m in msgs:
            m.is_deleted = True
            m.updated_at = datetime.now(UTC)

        await self.session.flush()
        return len(msgs)
