"""LangGraph 智能体编排图单元测试."""

from unittest.mock import AsyncMock, patch

import pytest

from src.agents.graph import (
    AGENT_PROMPTS,
    astream_chat,
    build_chat_workflow,
    llm_node,
    resolve_agent_intent,
    router_node,
)
from src.agents.state import AgentState


class TestAgentGraph:
    """智能体图逻辑测试类."""

    def test_resolve_agent_intent(self):
        """测试意图路由逻辑."""
        # 强制指定偏好优先
        assert resolve_agent_intent("hello", "code_assistant") == "code_assistant"
        assert resolve_agent_intent("def foo():", "deep_reasoner") == "deep_reasoner"

        # 自动识别代码偏好
        assert (
            resolve_agent_intent("How do I write a python function?", "auto")
            == "code_assistant"
        )
        assert (
            resolve_agent_intent("Fix this SQL bug please", "auto") == "code_assistant"
        )

        # 自动识别深度推理偏好
        assert (
            resolve_agent_intent("Why is the sky blue? Analyze deeply.", "auto")
            == "deep_reasoner"
        )
        assert resolve_agent_intent("请推导微积分公式", "auto") == "deep_reasoner"

        # 默认普通对话
        assert resolve_agent_intent("hi there", "auto") == "direct_chat"

    def test_router_node_basic(self):
        """测试 router 节点装配基本人设."""
        state: AgentState = {
            "messages": [{"role": "user", "content": "hello"}],
            "agent_preference": "direct_chat",
        }
        res = router_node(state)
        assert res["resolved_agent"] == "direct_chat"
        assert len(res["messages"]) == 2
        assert res["messages"][0]["role"] == "system"
        assert AGENT_PROMPTS["direct_chat"] in res["messages"][0]["content"]
        assert res["messages"][1]["content"] == "hello"

    def test_router_node_custom_prompt(self):
        """测试 router 节点附加用户自定义系统提示词."""
        state: AgentState = {
            "messages": [{"role": "user", "content": "help me with python"}],
            "agent_preference": "auto",
            "system_prompt": "Always reply in Chinese.",
        }
        res = router_node(state)
        assert res["resolved_agent"] == "code_assistant"
        assert "Always reply in Chinese." in res["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_llm_node(self):
        """测试 llm 调用节点."""
        state: AgentState = {
            "messages": [{"role": "user", "content": "hi"}],
            "model": "deepseek-v4-flash",
        }

        mock_resp = {
            "content": "Hello from mock",
            "usage": {"total_tokens": 15},
        }

        with patch("src.agents.graph.get_litellm_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.acompletion.return_value = mock_resp
            mock_get_client.return_value = mock_client

            output = await llm_node(state)
            assert output["final_response"] == "Hello from mock"
            assert output["metadata"]["usage"]["total_tokens"] == 15

    def test_build_chat_workflow(self):
        """测试构建 LangGraph StateGraph 并成功编译."""
        graph = build_chat_workflow()
        assert graph is not None
        assert hasattr(graph, "invoke") or hasattr(graph, "ainvoke")

    @pytest.mark.asyncio
    async def test_astream_chat(self):
        """测试 astream_chat 流式生成器."""
        mock_client = AsyncMock()

        async def mock_stream(*args, **kwargs):
            yield {"delta": "Hello", "finish_reason": None, "model": "m1"}
            yield {"delta": " World", "finish_reason": "stop", "model": "m1"}

        mock_client.astream_completion = mock_stream

        chunks = []
        async for c in astream_chat(
            messages=[{"role": "user", "content": "hi"}],
            model="m1",
            agent_preference="direct_chat",
            litellm_client=mock_client,
        ):
            chunks.append(c)

        assert len(chunks) == 2
        assert chunks[0]["delta"] == "Hello"
        assert chunks[0]["agent"] == "direct_chat"
        assert chunks[1]["delta"] == " World"
        assert chunks[1]["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_astream_chat_with_stop_checker(self):
        """测试 astream_chat 接收到外部中断信号."""
        mock_client = AsyncMock()

        async def mock_stream(*args, **kwargs):
            yield {"delta": "Chunk1", "finish_reason": None, "model": "m1"}
            yield {"delta": "Chunk2", "finish_reason": None, "model": "m1"}

        mock_client.astream_completion = mock_stream

        # 第二次检查返回 True 中断
        call_count = 0

        def stop_checker():
            nonlocal call_count
            call_count += 1
            return call_count >= 2

        chunks = []
        async for c in astream_chat(
            messages=[{"role": "user", "content": "hi"}],
            model="m1",
            agent_preference="auto",
            stop_checker=stop_checker,
            litellm_client=mock_client,
        ):
            chunks.append(c)

        assert len(chunks) == 2
        assert chunks[0]["delta"] == "Chunk1"
        assert chunks[1]["finish_reason"] == "stop"
