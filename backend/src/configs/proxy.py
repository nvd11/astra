"""代理配置模块.

用于本地开发环境配置 HTTP/HTTPS 代理.
"""

import os

from loguru import logger


def apply_proxy(http_proxy: str | None = None, https_proxy: str | None = None) -> None:
    """应用代理设置到环境变量.

    Args:
        http_proxy: HTTP 代理地址
        https_proxy: HTTPS 代理地址
    """
    if http_proxy:
        os.environ["HTTP_PROXY"] = http_proxy
        os.environ["http_proxy"] = http_proxy
        logger.info(f"HTTP proxy set: {http_proxy}")

    if https_proxy:
        os.environ["HTTPS_PROXY"] = https_proxy
        os.environ["https_proxy"] = https_proxy
        logger.info(f"HTTPS proxy set: {https_proxy}")


def clear_proxy() -> None:
    """清除代理设置."""
    for var in ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"]:
        os.environ.pop(var, None)
    logger.info("Proxy settings cleared")
