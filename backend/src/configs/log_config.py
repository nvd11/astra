"""Loguru 日志配置模块.

根据应用环境配置不同的日志输出格式.
"""

import json
import sys
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from loguru import Record


def setup_logging(app_env: str = "local") -> None:
    """配置 Loguru 日志器.

    Args:
        app_env: 应用环境 (local/dev/prod)
    """
    # 移除默认 handler
    logger.remove()

    if app_env == "prod":
        # 生产环境: JSON 结构化日志 (兼容 GCP Cloud Logging)
        def gcp_formatter(record: "Record") -> str:
            log_entry = {
                "severity": record["level"].name,
                "message": record["message"],
                "timestamp": record["time"].isoformat(),
                "logging.googleapis.com/sourceLocation": {
                    "file": record["file"].path,
                    "line": record["line"],
                    "function": record["function"],
                },
            }
            # 添加额外字段
            if record["extra"]:
                log_entry.update(record["extra"])
            record["extra"]["json_message"] = json.dumps(log_entry)
            return "{extra[json_message]}\n"

        logger.add(
            sys.stdout,
            format=gcp_formatter,
            level="INFO",
            backtrace=False,
            diagnose=False,
        )
        logger.info("Loguru configured for production (JSON output)")

    elif app_env == "dev":
        # 开发环境: 彩色输出到 stderr，包含更多调试信息
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>",
            level="DEBUG",
            backtrace=True,
            diagnose=True,
        )
        logger.info("Loguru configured for development (colorized output)")

    else:
        # 本地环境: 简洁输出
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<level>{message}</level>",
            level="DEBUG",
        )
        logger.info("Loguru configured for local development")


def get_logger(name: str) -> Any:
    """获取命名日志器.

    Args:
        name: 日志器名称

    Returns:
        Logger: Loguru 日志器实例
    """
    return logger.bind(name=name)
