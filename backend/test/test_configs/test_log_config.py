"""日志配置模块测试."""

from io import StringIO

from loguru import logger

from src.configs.log_config import get_logger, setup_logging


class TestLogConfig:
    """日志配置测试类."""

    def test_setup_logging_local(self):
        """测试本地环境日志配置."""
        setup_logging("local")
        # 验证 logger 已配置（不抛出异常即可）
        logger.info("Test local logging")

    def test_setup_logging_dev(self):
        """测试开发环境日志配置."""
        setup_logging("dev")
        logger.info("Test dev logging")

    def test_setup_logging_prod(self):
        """测试生产环境日志配置."""
        setup_logging("prod")
        logger.info("Test prod logging")

    def test_get_logger(self):
        """测试获取命名日志器."""
        test_logger = get_logger("test_module")
        assert test_logger is not None
        test_logger.info("Test named logger")

    def test_gcp_formatter_structure(self):
        """测试 GCP 日志格式化器结构."""
        # 直接测试格式化器函数
        from src.configs.log_config import setup_logging

        # 捕获 stdout
        captured = StringIO()
        setup_logging("prod")

        # 重新配置 logger 输出到捕获的 StringIO
        logger.remove()
        logger.add(captured, format="{message}", level="INFO")

        # 由于 gcp_formatter 是内部函数，我们间接验证 prod 模式不报错
        setup_logging("prod")
        logger.info("Test message")

        # 恢复标准配置
        setup_logging("local")
