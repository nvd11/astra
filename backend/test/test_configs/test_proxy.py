"""代理配置模块测试."""

import os

from src.configs.proxy import apply_proxy, clear_proxy


class TestProxy:
    """代理配置测试类."""

    def test_apply_proxy_both(self):
        """测试同时设置 HTTP 和 HTTPS 代理."""
        apply_proxy("http://proxy.local:7890", "https://proxy.local:7890")
        assert os.environ.get("HTTP_PROXY") == "http://proxy.local:7890"
        assert os.environ.get("http_proxy") == "http://proxy.local:7890"
        assert os.environ.get("HTTPS_PROXY") == "https://proxy.local:7890"
        assert os.environ.get("https_proxy") == "https://proxy.local:7890"
        clear_proxy()

    def test_apply_proxy_http_only(self):
        """测试仅设置 HTTP 代理."""
        apply_proxy(http_proxy="http://proxy.local:7890")
        assert os.environ.get("HTTP_PROXY") == "http://proxy.local:7890"
        assert os.environ.get("HTTPS_PROXY") is None
        clear_proxy()

    def test_apply_proxy_https_only(self):
        """测试仅设置 HTTPS 代理."""
        apply_proxy(https_proxy="https://proxy.local:7890")
        assert os.environ.get("HTTP_PROXY") is None
        assert os.environ.get("HTTPS_PROXY") == "https://proxy.local:7890"
        clear_proxy()

    def test_apply_proxy_none(self):
        """测试不设置任何代理."""
        apply_proxy()
        assert os.environ.get("HTTP_PROXY") is None
        assert os.environ.get("HTTPS_PROXY") is None

    def test_clear_proxy(self):
        """测试清除代理设置."""
        os.environ["HTTP_PROXY"] = "http://proxy.local:7890"
        os.environ["http_proxy"] = "http://proxy.local:7890"
        os.environ["HTTPS_PROXY"] = "https://proxy.local:7890"
        os.environ["https_proxy"] = "https://proxy.local:7890"

        clear_proxy()

        assert os.environ.get("HTTP_PROXY") is None
        assert os.environ.get("http_proxy") is None
        assert os.environ.get("HTTPS_PROXY") is None
        assert os.environ.get("https_proxy") is None
