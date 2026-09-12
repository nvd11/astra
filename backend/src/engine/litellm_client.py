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
        # 自动丢弃推理模型 (如 o1/o3/luna-yuanheng) 不支持的特定参数 (如 temperature)
        litellm.drop_params = True

        logger.info(
            f"LiteLLM client initialized with gateway={self.base_url}, default_model={self.default_model}"
        )

    def _normalize_model(self, model: str | None) -> str:
        """规范化模型标识.

        直连统一 OpenAI 兼容私有网关时，去除提供商前缀以精确匹配网关中注册的模型标识.

        Args:
            model: 用户或请求传入的模型名称

        Returns:
            str: 格式化后的模型标识
        """
        target_model = model or self.default_model
        if target_model.startswith("openai/"):
            return target_model[len("openai/") :]
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
                custom_llm_provider="openai",
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
        """流式异步补全生成器 (支持通用 LLM 与 Hermes Agent 无损直通).

        Args:
            messages: OpenAI 格式消息列表
            model: 模型名称
            temperature: 采样温度
            max_tokens: 最大生成 Token
            **kwargs: 额外参数

        Yields:
            dict: 包含增量 delta, finish_reason, model, tool_progress 的字典
        """
        formatted_model = self._normalize_model(model)
        logger.debug(f"LiteLLM astream_completion start: model={formatted_model}")

        # 🎯 针对 Hermes Agent (rin / yui) 使用 LiteLLM 直通路由，完整接收自定义 SSE 事件
        normalized_lower = formatted_model.lower()
        if normalized_lower in ("rin", "yui"):
            async for chunk in self._astream_hermes_passthrough(
                messages=messages,
                agent_name=normalized_lower,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            ):
                yield chunk
            return

        try:
            response = await litellm.acompletion(
                model=formatted_model,
                custom_llm_provider="openai",
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

    async def _astream_hermes_passthrough(
        self,
        messages: list[dict[str, str]],
        agent_name: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """通过 LiteLLM /hermes/{agent}/v1/chat/completions 无损消费 SSE 原生流."""
        import json
        import httpx

        # 兼容带 /v1 或不带 /v1 的 base_url
        base = self.base_url.rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]

        url = f"{base}/hermes/{agent_name}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "model": agent_name,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        logger.info(f"Connecting to Hermes Agent via LiteLLM passthrough: {url}")
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    current_event = None
                    async for line in response.aiter_lines():
                        if not line:
                            current_event = None
                            continue

                        line_str = line.strip()
                        if line_str.startswith("event:"):
                            current_event = line_str[6:].strip()
                            continue

                        if line_str.startswith("data:"):
                            raw_data = line_str[5:].strip()
                            if raw_data == "[DONE]":
                                break

                            try:
                                data_obj = json.loads(raw_data)
                            except Exception:
                                continue

                            # 🎯 自定义工具流事件
                            if current_event == "hermes.tool.progress":
                                yield {
                                    "delta": "",
                                    "tool_progress": data_obj,
                                    "finish_reason": None,
                                    "model": agent_name,
                                }
                                continue

                            # 🎯 标准 OpenAI ChatCompletionChunk
                            choices = data_obj.get("choices", [])
                            if choices:
                                choice = choices[0]
                                delta = choice.get("delta", {})
                                content = delta.get("content", "")
                                finish_reason = choice.get("finish_reason")
                                # 忽略首帧空的 role="assistant" 帧，避免下发空增量
                                if not content and not finish_reason:
                                    continue
                                yield {
                                    "delta": content,
                                    "finish_reason": finish_reason,
                                    "model": data_obj.get("model", agent_name),
                                }

        except Exception as err:
            logger.error(f"Hermes passthrough stream error: {err}")
            raise

    async def get_models(self) -> list[dict[str, Any]]:
        """从 LiteLLM 网关动态拉取当前挂载的真实模型列表.

        Returns:
            list[dict[str, Any]]: 模型元数据字典列表
        """
        import httpx

        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        logger.debug(f"Querying LiteLLM gateway models: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                raw_models: list[dict[str, Any]] = data.get("data", [])
                logger.info(f"Discovered {len(raw_models)} models from LiteLLM gateway")
                return raw_models
        except Exception as err:
            logger.error(f"Failed to fetch models from LiteLLM gateway: {err}")
            return []


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
