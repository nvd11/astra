"""配置加载模块测试."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.configs.config import (
    APP_ENV,
    PROJECT_PATH,
    Settings,
    _load_yaml_config,
    _setup_project_path,
    get_settings,
)


class TestConfig:
    """配置加载测试类."""

    def test_setup_project_path(self):
        """测试项目路径设置."""
        path = _setup_project_path()
        assert isinstance(path, Path)
        assert path.name == "backend"

    def test_load_yaml_config_local(self):
        """测试加载本地环境 YAML 配置."""
        config = _load_yaml_config("local")
        assert isinstance(config, dict)
        assert "server" in config
        assert config["server"]["host"] == "0.0.0.0"
        assert config["server"]["port"] == 8000
        assert config["server"]["workers"] == 1

    def test_load_yaml_config_dev(self):
        """测试加载开发环境 YAML 配置."""
        config = _load_yaml_config("dev")
        assert isinstance(config, dict)
        assert config["server"]["root_path"] == "/api"

    def test_load_yaml_config_prod(self):
        """测试加载生产环境 YAML 配置."""
        config = _load_yaml_config("prod")
        assert isinstance(config, dict)
        assert config["server"]["workers"] == 4
        assert config["logging"]["level"] == "INFO"

    def test_load_yaml_config_not_found(self):
        """测试加载不存在的 YAML 配置."""
        config = _load_yaml_config("nonexistent")
        assert config == {}

    def test_settings_default_values(self):
        """测试 Settings 默认值."""
        # 清除可能的环境变量影响，确保测试默认值
        env_vars_to_clear = [
            "APP_NAME",
            "APP_VERSION",
            "APP_ENVIRONMENT",
            "APP_DEBUG",
            "APP_HOST",
            "APP_PORT",
            "APP_WORKERS",
            "APP_ROOT_PATH",
            "APP_LOG_LEVEL",
            "APP_DATABASE_URL",
            "APP_REDIS_URL",
            "APP_LITELLM_BASE_URL",
            "APP_LITELLM_API_KEY",
            "APP_DEFAULT_MODEL",
            "APP_JWT_SECRET",
            "APP_JWT_ALGORITHM",
            "APP_JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
            "APP_JWT_REFRESH_TOKEN_EXPIRE_DAYS",
            "APP_LOGTO_ENDPOINT",
            "APP_LOGTO_APP_ID",
            "APP_LOGTO_APP_SECRET",
            "APP_LOGTO_REDIRECT_URI",
        ]
        with patch.dict(os.environ, dict.fromkeys(env_vars_to_clear, ""), clear=False):
            # 移除空字符串环境变量，让 pydantic 使用默认值
            for var in env_vars_to_clear:
                os.environ.pop(var, None)
            settings = Settings(_env_file=None)
        assert settings.app_name == "Astra"
        assert settings.app_version == "1.0.0"
        assert settings.app_environment == "local"
        assert settings.debug is False
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.workers == 1
        assert settings.root_path == ""
        assert settings.log_level == "INFO"
        assert (
            settings.database_url
            == "mysql+asyncmy://astra_user:astra_pass@127.0.0.1:3306/astra"
        )
        assert settings.redis_url == "redis://:hsbc1234@127.0.0.1:6379/0"
        assert settings.litellm_base_url == "https://litellm.jppwl.asia"
        assert settings.default_model == "deepseek-v4-flash"
        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_access_token_expire_minutes == 120
        assert settings.jwt_refresh_token_expire_days == 7
        assert settings.logto_endpoint == "https://auth.jppwl.asia"
        assert settings.logto_redirect_uri == "https://astra.jppwl.asia/callback"

    def test_settings_from_yaml(self):
        """测试从 YAML 创建 Settings."""
        yaml_config = {
            "server": {
                "host": "127.0.0.1",
                "port": 9000,
                "workers": 2,
                "root_path": "/api",
            },
            "logging": {
                "level": "DEBUG",
            },
        }
        settings = Settings.from_yaml(yaml_config)
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.workers == 2
        assert settings.root_path == "/api"
        assert settings.log_level == "DEBUG"

    def test_settings_validate_log_level_valid(self):
        """测试日志级别校验 - 有效值."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "debug", "info"]:
            settings = Settings(log_level=level)
            assert settings.log_level == level.upper()

    def test_settings_validate_log_level_invalid(self):
        """测试日志级别校验 - 无效值."""
        with pytest.raises(ValueError, match="Log level must be one of"):
            Settings(log_level="INVALID")

    def test_settings_env_override(self):
        """测试环境变量覆盖 YAML 配置."""
        with patch.dict(os.environ, {"APP_PORT": "9999", "APP_DEBUG": "true"}):
            settings = Settings()
            assert settings.port == 9999
            assert settings.debug is True

    def test_get_settings_singleton(self):
        """测试 get_settings 单例模式."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_app_env_constant(self):
        """测试 APP_ENV 常量."""
        assert APP_ENV == "local"

    def test_project_path_constant(self):
        """测试 PROJECT_PATH 常量."""
        assert isinstance(PROJECT_PATH, Path)
        assert PROJECT_PATH.name == "backend"
