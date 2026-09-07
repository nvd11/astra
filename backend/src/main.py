"""FastAPI 应用工厂模块."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.configs.config import APP_ENV, get_settings
from src.engine.mysql_client import get_mysql_client
from src.engine.redis_client import get_redis_client
from src.routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期管理."""
    settings = get_settings()

    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {APP_ENV}")

    # 初始化存储连接池
    app.state.mysql_client = get_mysql_client()
    app.state.redis_client = get_redis_client()

    # 验证连通性
    mysql_ok = await app.state.mysql_client.check_connection()
    redis_ok = await app.state.redis_client.ping()

    if not mysql_ok:
        logger.warning("MySQL connection failed during startup")
    if not redis_ok:
        logger.warning("Redis connection failed during startup")

    yield

    # 优雅关闭
    logger.info("Shutting down storage connections...")
    await app.state.mysql_client.close()
    await app.state.redis_client.close()
    logger.info("Application shutdown complete.")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例.

    Returns:
        FastAPI: 配置完成的应用实例
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Modern LLM Chat Backend with FastAPI, LangGraph, and MySQL HeatWave",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        root_path=settings.root_path,
        lifespan=lifespan,
    )

    # CORS 配置 (从统一 Settings 体系加载)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 企业级治理中间件 (遵循洋葱模型：RequestID 在最外层)
    from src.middleware.request_id import RequestIDMiddleware
    from src.middleware.timing import TimingMiddleware

    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # 注册路由
    app.include_router(api_router)

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "Internal server error",
                "data": None,
            },
        )

    return app


# 创建应用实例
app = create_app()
