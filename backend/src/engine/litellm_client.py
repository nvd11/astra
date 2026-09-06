"""LiteLLM 客户端封装模块.

连接私有 LiteLLM 网关 (https://litellm.jppwl.asia)，提供统一异步 LLM 调用与流式推理.
"""

from collections.abc import AsyncIterator
from typing import Any

import litellm
from loguru import logger

from src.configs.config import Settings, get_settings


class LiteLLMClient:
    """LiteLLM 网关异步客户端."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        default_model: str = "deepseek-v4-flash",
    ) -> None:
        """初始化 LiteLLM 客户端.

        Args:
            base_url: LiteLLM 网关基础地址
            api_key: 网关访问密钥
            default_model: 默认模型名称
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model

        # 禁用 LiteLLM 的 telemetry 收集以保护金融环境数据合规
        litellm.telemetry = False

        logger.info(
            f"LiteLLM client initialized with gateway={self.base_url}, default_model={self.default_model}"
        )

    def _normalize_model(self, model: str | None) -> str:
        """规范化模型标识.

        若模型未包含提供商前缀，且连接至统一 OpenAI 兼容网关，补充 openai/ 前缀.

        Args:
            model: 用户或请求传入的模型名称

        Returns:
            str: 格式化后的模型标识
        """
        target_model = model or self.default_model
        if "/" not in target_model:
            return f"openai/{target_model}"
        return target_model

    async def acompletion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """单次非流式异步补全.

        Args:
            messages: OpenAI 格式消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 采样温度
            max_tokens: 最大生成 Token
            **kwargs: 额外参数

        Returns:
            dict: 响应载荷 (包含 content, model, usage)
        """
        formatted_model = self._normalize_model(model)

        logger.debug(
            f"LiteLLM acompletion request: model={formatted_model}, msgs_len={len(messages)}"
        )

        try:
            response = await litellm.acompletion(
                model=formatted_model,
                messages=messages,
                api_base=self.base_url,
                api_key=self.api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs,
            )

            choice = response.choices[0]
            content = choice.message.content or ""
            finish_reason = choice.finish_reason

            usage = {}
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return {
                "content": content,
                "finish_reason": finish_reason,
                "model": response.model,
                "usage": usage,
            }
        except Exception as e:
            logger.error(f"LiteLLM acompletion failed: {e}")
            raise

    async def astream_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """流式异步补全生成器.

        Args:
            messages: OpenAI 格式消息列表
            model: 模型名称
            temperature: 采样温度
            max_tokens: 最大生成 Token
            **kwargs: 额外参数

        Yields:
            dict: 包含增量 delta, finish_reason, model 的字典
        """
        formatted_model = self._normalize_model(model)
        logger.debug(f"LiteLLM astream_completion start: model={formatted_model}")

        try:
            response = await litellm.acompletion(
                model=formatted_model,
                messages=messages,
                api_base=self.base_url,
                api_key=self.api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in response:
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                delta_content = ""
                if hasattr(choice, "delta") and choice.delta:
                    delta_content = getattr(choice.delta, "content", "") or ""

                finish_reason = getattr(choice, "finish_reason", None)

                yield {
                    "delta": delta_content,
                    "finish_reason": finish_reason,
                    "model": getattr(chunk, "model", formatted_model),
                }

        except Exception as e:
            logger.error(f"LiteLLM astream_completion failed: {e}")
            raise


# 全局单例
_litellm_client: LiteLLMClient | None = None


def get_litellm_client() -> LiteLLMClient:
    """获取 LiteLLM 客户端单例.

    Returns:
        LiteLLMClient: 客户端实例
    """
    global _litellm_client
    if _litellm_client is None:
        settings: Settings = get_settings()
        _litellm_client = LiteLLMClient(
            base_url=settings.litellm_base_url,
            api_key=settings.litellm_api_key,
            default_model=settings.default_model,
        )
    return _litellm_client
