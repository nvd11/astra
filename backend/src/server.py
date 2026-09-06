"""Astra Backend 服务启动入口.

使用方式:
    uv run python -m src.server
    或
    uvicorn src.server:app --host 0.0.0.0 --port 8000
    或
    python src/server.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径 (支持直接运行)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from src.configs.config import APP_ENV, get_settings


def main() -> None:
    """主入口函数."""
    settings = get_settings()

    logger.info(f"Starting {settings.app_name} server...")
    logger.info(f"Environment: {APP_ENV}")
    logger.info(f"Listening on {settings.host}:{settings.port}")

    import uvicorn

    uvicorn.run(
        "src.server:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
