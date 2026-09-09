"""配置加载器模块.

负责加载环境变量、YAML 配置文件，并初始化日志系统.
"""

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from loguru import logger
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .log_config import setup_logging
from .proxy import apply_proxy


# ====================== 项目路径设置 =======================
def _setup_project_path() -> Path:
    """设置项目路径并添加到 sys.path.

    Returns:
        Path: 项目根目录路径
    """
    script_path = Path(__file__).resolve()
    project_path = script_path.parent.parent.parent
    sys.path.insert(0, str(project_path))
    return project_path


PROJECT_PATH = _setup_project_path()


# ================== 加载环境变量 =======================
load_dotenv(override=True)

# 获取应用环境，默认为 'local'
APP_ENV = os.getenv("APP_ENVIRONMENT", "local")

# 配置日志
setup_logging(APP_ENV)

logger.info(f"Application Environment (APP_ENVIRONMENT): '{APP_ENV}'")


# ================== 加载 YAML 配置 =======================
def _load_yaml_config(env: str) -> dict[str, Any]:
    """根据环境加载 YAML 配置文件.

    Args:
        env: 环境名称 (local/dev/prod)

    Returns:
        dict: 配置字典
    """
    config_file = PROJECT_PATH / "src" / "configs" / f"config_{env}.yaml"

    logger.info(f"Loading configuration from: {config_file}")

    try:
        with open(config_file) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        logger.info(f"Successfully loaded {config_file.name}")
        return config or {}
    except FileNotFoundError:
        logger.warning(f"Configuration file not found: {config_file}, using defaults")
        return {}


YAML_CONFIG = _load_yaml_config(APP_ENV)


# ================== 代理设置 (本地环境) =======================
if APP_ENV == "local" and YAML_CONFIG.get("proxy"):
    proxy_settings = YAML_CONFIG["proxy"]
    apply_proxy(
        http_proxy=proxy_settings.get("http"), https_proxy=proxy_settings.get("https")
    )


# ================== 配置类定义 =======================
class Settings(BaseSettings):
    """应用配置类.

    结合 YAML 配置和环境变量，提供类型安全的配置访问.
    环境变量优先级高于 YAML 配置.
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ========== 基础服务配置 ==========
    app_name: str = Field(default="Astra", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    app_environment: str = Field(default="local", description="运行环境")
    debug: bool = Field(default=False, description="调试模式")

    # ========== 服务器配置 ==========
    host: str = Field(default="0.0.0.0", description="监听主机")
    port: int = Field(default=8000, ge=1, le=65535, description="监听端口")
    workers: int = Field(default=1, ge=1, le=8, description="Worker 数量")
    root_path: str = Field(default="", description="API 根路径")

    # ========== CORS 跨域配置 ==========
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "https://astra.jppwl.asia",
            "http://localhost:3000",
            "http://localhost:5173",
        ],
        description="跨域允许的来源列表",
    )

    # ========== 日志配置 ==========
    log_level: str = Field(default="INFO", description="日志级别")

    # ========== 数据库配置 (OCI MySQL HeatWave) ==========
    database_url: str = Field(
        default="mysql+asyncmy://astra_user:placeholder_pass@127.0.0.1:3306/astra",
        description="MySQL HeatWave 异步连接串",
    )

    # ========== 缓存配置 (Redis) ==========
    redis_url: str = Field(
        default="redis://127.0.0.1:6379/0", description="Redis 连接串"
    )

    # ========== 私有 LiteLLM 网关 ==========
    litellm_base_url: str = Field(
        default="https://litellm.jppwl.asia", description="LiteLLM 网关地址"
    )
    litellm_api_key: str = Field(
        default="sk-placeholder-litellm-key", description="LiteLLM 网关密钥"
    )
    default_model: str = Field(default="deepseek-v4-flash", description="默认 LLM 模型")

    # ========== JWT 认证与会话安全 ==========
    jwt_secret: str = Field(
        default="change-this-to-a-super-secret-random-key-in-production",
        description="JWT 签名密钥",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT 加密算法")
    jwt_access_token_expire_minutes: int = Field(
        default=120, description="Access Token 过期时间 (分钟)"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="Refresh Token 过期时间 (天)"
    )

    # ========== 认证开关 (支持 Cloudflare 同域部署与 Kong Forward-Auth) ==========
    auth_enabled: bool = Field(
        default=True, description="是否启用认证 (false 时跳过 JWT/Logto 校验)"
    )
    auth_mode: str = Field(
        default="forward-auth",
        description="认证模式: forward-auth | logto | cloudflare | none",
    )
    cloudflare_team_name: str = Field(
        default="",
        description="Cloudflare Access Team Name (用于验证 CF-Access-Jwt-Assertion)",
    )
    cloudflare_audience: str = Field(
        default="", description="Cloudflare Access Audience (AUD)"
    )

    # ========== Logto SSO 统一认证 ==========
    logto_endpoint: str = Field(
        default="https://auth.jppwl.asia", description="Logto SSO 端点"
    )
    logto_app_id: str = Field(default="", description="Logto 应用 ID")
    logto_app_secret: str = Field(default="", description="Logto 应用密钥")
    logto_redirect_uri: str = Field(
        default="https://astra.jppwl.asia/callback", description="Logto 回调地址"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """校验日志级别."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v

    @field_validator("auth_mode")
    @classmethod
    def validate_auth_mode(cls, v: str) -> str:
        """校验认证模式."""
        valid_modes = {"forward-auth", "logto", "cloudflare", "none"}
        v = v.lower()
        if v not in valid_modes:
            raise ValueError(f"Auth mode must be one of {valid_modes}")
        return v

    @classmethod
    def from_yaml(cls, yaml_config: dict[str, Any]) -> "Settings":
        """从 YAML 配置创建 Settings 实例.

        Args:
            yaml_config: YAML 配置字典

        Returns:
            Settings: 配置实例
        """
        flat_config: dict[str, Any] = {}

        # 服务配置
        if "server" in yaml_config:
            server = yaml_config["server"]
            flat_config["host"] = server.get("host", "0.0.0.0")
            flat_config["port"] = server.get("port", 8000)
            flat_config["workers"] = server.get("workers", 1)
            flat_config["root_path"] = server.get("root_path", "")

        # 日志配置
        if "logging" in yaml_config:
            logging_config = yaml_config["logging"]
            flat_config["log_level"] = logging_config.get("level", "INFO")

        return cls(**flat_config)


@lru_cache
def get_settings() -> Settings:
    """获取应用配置单例.

    Returns:
        Settings: 应用配置实例
    """
    return Settings.from_yaml(YAML_CONFIG)


# 导出常用配置
__all__ = ["APP_ENV", "YAML_CONFIG", "Settings", "get_settings", "PROJECT_PATH"]
