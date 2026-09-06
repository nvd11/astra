"""API 路由模块初始化."""

from fastapi import APIRouter

from . import auth, chat, conversations, health, sessions, users

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router)
api_router.include_router(sessions.router)
api_router.include_router(conversations.router)
api_router.include_router(chat.router)
api_router.include_router(users.router)

__all__ = ["api_router"]
