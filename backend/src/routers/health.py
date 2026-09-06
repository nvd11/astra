"""健康检查路由模块."""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from loguru import logger

from src.configs.config import Settings, get_settings
from src.engine.mysql_client import get_mysql_client
from src.engine.redis_client import get_redis_client
from src.models.responses import HealthResponse, HealthResponseData

router = APIRouter()

# 服务启动时间
_start_time = time.time()


def get_settings_dep() -> Settings:
    """获取配置依赖."""
    return get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="Kubernetes 探针健康检查端点",
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings_dep)],
    detailed: Annotated[bool, Query(description="是否返回详细信息")] = False,
) -> HealthResponse:
    """健康检查端点.

    Args:
        settings: 应用配置
        detailed: 是否返回详细健康信息

    Returns:
        HealthResponse: 健康检查响应
    """
    mysql_client = get_mysql_client()
    redis_client = get_redis_client()

    mysql_ok = await mysql_client.check_connection()
    redis_ok = await redis_client.ping()

    status = "ok" if (mysql_ok and redis_ok) else "error"

    data = HealthResponseData(
        status=status,
        service=settings.app_name,
        version=settings.app_version,
        mysql_ok=mysql_ok,
        redis_ok=redis_ok,
        uptime_seconds=round(time.time() - _start_time, 2) if detailed else None,
    )

    logger.debug(f"Health check: status={status}, mysql={mysql_ok}, redis={redis_ok}")

    return HealthResponse(data=data)


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="就绪检查",
    description="Kubernetes 就绪探针",
)
async def readiness_check(
    settings: Annotated[Settings, Depends(get_settings_dep)]
) -> HealthResponse:
    """就绪检查端点."""
    return await health_check(settings, detailed=False)


@router.get(
    "/live",
    response_model=HealthResponse,
    summary="存活检查",
    description="Kubernetes 存活探针",
)
async def liveness_check(
    settings: Annotated[Settings, Depends(get_settings_dep)]
) -> HealthResponse:
    """存活检查端点."""
    data = HealthResponseData(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        mysql_ok=True,
        redis_ok=True,
        uptime_seconds=None,
    )
    return HealthResponse(data=data)
