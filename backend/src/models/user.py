"""用户模型与数据库操作模块.

基于 SQLAlchemy 2.0 异步 ORM 实现用户表与会话表的数据库操作.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类."""

    pass


class User(Base):
    """用户表模型."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    default_model: Mapped[str] = mapped_column(String(64), default="deepseek-v4-flash")
    default_agent: Mapped[str] = mapped_column(String(64), default="auto")
    logto_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class UserSession(Base):
    """用户设备会话表模型."""

    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    device_info: Mapped[str] = mapped_column(String(255), default="Unknown Device")
    ip_address: Mapped[str] = mapped_column(String(45), default="0.0.0.0")
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class UserRepository:
    """用户数据仓库."""

    def __init__(self, session: AsyncSession) -> None:
        """初始化用户仓库.

        Args:
            session: 数据库异步会话
        """
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        """根据 ID 查询用户.

        Args:
            user_id: 用户 ID

        Returns:
            User | None: 用户对象
        """
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """根据用户名查询用户.

        Args:
            username: 用户名

        Returns:
            User | None: 用户对象
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_logto_id(self, logto_id: str) -> User | None:
        """根据 Logto ID 查询用户.

        Args:
            logto_id: Logto 用户 ID

        Returns:
            User | None: 用户对象
        """
        result = await self.session.execute(
            select(User).where(User.logto_id == logto_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        username: str,
        email: str | None = None,
        avatar_url: str | None = None,
        logto_id: str | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> User:
        """创建新用户.

        Args:
            username: 用户名
            email: 邮箱
            avatar_url: 头像 URL
            logto_id: Logto 用户 ID
            preferences: 用户偏好

        Returns:
            User: 创建的用户对象
        """
        user = User(
            username=username,
            email=email,
            avatar_url=avatar_url,
            logto_id=logto_id,
            preferences=preferences or {},
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(
        self,
        user_id: str,
        **kwargs: Any,
    ) -> User | None:
        """更新用户信息.

        Args:
            user_id: 用户 ID
            **kwargs: 更新字段

        Returns:
            User | None: 更新后的用户对象
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_or_create_by_logto(
        self,
        logto_id: str,
        username: str,
        email: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """根据 Logto 信息获取或创建用户.

        Args:
            logto_id: Logto 用户 ID
            username: 用户名
            email: 邮箱
            avatar_url: 头像 URL

        Returns:
            User: 用户对象
        """
        user = await self.get_by_logto_id(logto_id)
        if user:
            # 更新最新信息
            await self.update(
                user.id,
                username=username,
                email=email,
                avatar_url=avatar_url,
            )
            return user

        # 检查用户名是否已存在
        existing = await self.get_by_username(username)
        if existing:
            # 绑定 Logto ID 到已有用户
            await self.update(existing.id, logto_id=logto_id)
            return existing

        # 创建新用户
        return await self.create(
            username=username,
            email=email,
            avatar_url=avatar_url,
            logto_id=logto_id,
        )


class SessionRepository:
    """用户会话数据仓库."""

    def __init__(self, session: AsyncSession) -> None:
        """初始化会话仓库.

        Args:
            session: 数据库异步会话
        """
        self.session = session

    async def create(
        self,
        user_id: str,
        refresh_token: str,
        device_info: str = "Unknown Device",
        ip_address: str = "0.0.0.0",
        expires_at: datetime | None = None,
    ) -> UserSession:
        """创建用户会话.

        Args:
            user_id: 用户 ID
            refresh_token: Refresh Token
            device_info: 设备信息
            ip_address: IP 地址
            expires_at: 过期时间

        Returns:
            UserSession: 会话对象
        """
        if expires_at is None:
            expires_at = datetime.now(UTC)

        session = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            expires_at=expires_at,
        )
        self.session.add(session)
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def get_by_refresh_token(self, refresh_token: str) -> UserSession | None:
        """根据 Refresh Token 查询会话.

        Args:
            refresh_token: Refresh Token

        Returns:
            UserSession | None: 会话对象
        """
        result = await self.session.execute(
            select(UserSession).where(UserSession.refresh_token == refresh_token)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> list[UserSession]:
        """查询用户的所有活跃会话.

        Args:
            user_id: 用户 ID

        Returns:
            list[UserSession]: 会话列表
        """
        result = await self.session.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.last_active_at.desc())
        )
        return list(result.scalars().all())

    async def delete_by_refresh_token(self, refresh_token: str) -> bool:
        """根据 Refresh Token 删除会话.

        Args:
            refresh_token: Refresh Token

        Returns:
            bool: 是否删除成功
        """
        session = await self.get_by_refresh_token(refresh_token)
        if not session:
            return False
        await self.session.delete(session)
        await self.session.flush()
        return True

    async def delete_by_id(self, session_id: str, user_id: str) -> bool:
        """根据会话 ID 和用户 ID 删除会话 (行级隔离单句原子删除).

        Args:
            session_id: 会话记录 ID
            user_id: 所属用户 ID

        Returns:
            bool: 是否删除成功
        """
        stmt = delete(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return (getattr(result, "rowcount", 0) or 0) > 0

    async def delete_by_user_id(
        self, user_id: str, exclude_current: str | None = None
    ) -> int:
        """删除用户的所有会话 (可选排除当前会话，单句原子批量删除).

        Args:
            user_id: 用户 ID
            exclude_current: 要排除的 Refresh Token

        Returns:
            int: 删除的会话数量
        """
        stmt = delete(UserSession).where(UserSession.user_id == user_id)
        if exclude_current:
            stmt = stmt.where(UserSession.refresh_token != exclude_current)

        result = await self.session.execute(stmt)
        await self.session.flush()
        return int(getattr(result, "rowcount", 0) or 0)
