"""LiteLLM 客户端单元测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.engine.litellm_client import LiteLLMClient, get_litellm_client


class TestLiteLLMClient:
    """LiteLLM 客户端测试类."""

    @pytest.fixture
    def client(self):
        """客户端测试 fixture."""
        return LiteLLMClient(
            base_url="https://litellm.test.local",
            api_key="sk-test-key",
            default_model="deepseek-v4-flash",
        )

    def test_init(self, client):
        """测试初始化属性."""
        assert client.base_url == "https://litellm.test.local"
        assert client.api_key == "sk-test-key"
        assert client.default_model == "deepseek-v4-flash"

    def test_normalize_model(self, client):
        """测试模型前缀规范化."""
        assert (
            client._normalize_model("gpt-5.6-luna-yuanheng") == "gpt-5.6-luna-yuanheng"
        )
        assert client._normalize_model("openai/gpt-4o") == "gpt-4o"
        assert client._normalize_model(None) == "deepseek-v4-flash"

    @pytest.mark.asyncio
    async def test_acompletion_success(self, client):
        """测试异步完整补全 - 成功."""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "你好！我是 Astra"
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_response.model = "deepseek-v4-flash"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_litellm:
            mock_litellm.return_value = mock_response

            res = await client.acompletion(
                messages=[{"role": "user", "content": "hi"}],
                model="deepseek-v4-flash",
            )

            assert res["content"] == "你好！我是 Astra"
            assert res["finish_reason"] == "stop"
            assert res["model"] == "deepseek-v4-flash"
            assert res["usage"]["total_tokens"] == 30
            mock_litellm.assert_called_once()

    @pytest.mark.asyncio
    async def test_acompletion_error(self, client):
        """测试异步完整补全 - 异常抛出."""
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_litellm:
            mock_litellm.side_effect = RuntimeError("LiteLLM gateway timeout")

            with pytest.raises(RuntimeError, match="LiteLLM gateway timeout"):
                await client.acompletion(messages=[{"role": "user", "content": "hi"}])

    @pytest.mark.asyncio
    async def test_astream_completion_success(self, client):
        """测试流式异步补全生成器 - 成功."""
        chunk1 = MagicMock()
        choice1 = MagicMock()
        choice1.delta.content = "Astra "
        choice1.finish_reason = None
        chunk1.choices = [choice1]
        chunk1.model = "deepseek-v4-flash"

        chunk2 = MagicMock()
        choice2 = MagicMock()
        choice2.delta.content = "回答完毕"
        choice2.finish_reason = "stop"
        chunk2.choices = [choice2]
        chunk2.model = "deepseek-v4-flash"

        async def mock_generator():
            yield chunk1
            yield chunk2

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_litellm:
            mock_litellm.return_value = mock_generator()

            results = []
            async for chunk in client.astream_completion(
                messages=[{"role": "user", "content": "hello"}]
            ):
                results.append(chunk)

            assert len(results) == 2
            assert results[0]["delta"] == "Astra "
            assert results[0]["finish_reason"] is None
            assert results[1]["delta"] == "回答完毕"
            assert results[1]["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_astream_completion_error(self, client):
        """测试流式异步补全生成器 - 异常中断."""
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_litellm:
            mock_litellm.side_effect = RuntimeError("Connection error")

            with pytest.raises(RuntimeError, match="Connection error"):
                async for _ in client.astream_completion(messages=[]):
                    pass

    @pytest.mark.asyncio
    async def test_get_models_success(self, client):
        """测试动态获取网关模型列表 - 成功."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"id": "gemini-3.8-flash", "object": "model"},
                {"id": "kimi-k3", "object": "model"},
            ]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            models = await client.get_models()
            assert len(models) == 2
            assert models[0]["id"] == "gemini-3.8-flash"
            assert models[1]["id"] == "kimi-k3"

    @pytest.mark.asyncio
    async def test_get_models_error(self, client):
        """测试动态获取网关模型列表 - 异常降级."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Gateway unreachable")
            models = await client.get_models()
            assert models == []


class TestGetLiteLLMClient:
    """get_litellm_client 单例测试."""

    def test_singleton(self):
        """测试全局单例获取."""
        import src.engine.litellm_client as module

        module._litellm_client = None

        with patch("src.engine.litellm_client.get_settings") as mock_settings:
            mock_s = MagicMock()
            mock_s.litellm_base_url = "https://litellm.test.local"
            mock_s.litellm_api_key = "key"
            mock_s.default_model = "deepseek-v4-flash"
            mock_settings.return_value = mock_s

            c1 = get_litellm_client()
            c2 = get_litellm_client()
            assert c1 is c2
