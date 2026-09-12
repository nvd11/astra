"""智能体编排与工作流图模块 (LangGraph StateGraph).

支持基于意图自动路由 (Auto Routing)、智能体分流与可中断的流式生成.
"""

from collections.abc import AsyncIterator, Callable
from typing import Any

from langgraph.graph import END, StateGraph
from loguru import logger

from src.agents.state import AgentState
from src.engine.litellm_client import LiteLLMClient, get_litellm_client

# 智能体系统预设人设
AGENT_PROMPTS: dict[str, str] = {
    "direct_chat": "You are Astra, a helpful, sophisticated, and friendly AI assistant.",
    "code_assistant": "You are an expert software engineer and systems architect. Provide concise, clean, and robust code with modern best practices.",
    "deep_reasoner": "You are a deep-thinking AI assistant. Analyze problems methodically, verifying edge cases and thinking step-by-step.",
}

# 智能体中心注册表 (作为全系统唯一信任源 SSOT，供动态 API 与前端消费)
AGENT_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "auto",
        "name": "自动路由",
        "description": "Main Agent 根据提问智能意图分发",
        "icon": "Sparkles",
        "is_default": True,
    },
    {
        "id": "code_assistant",
        "name": "代码助手",
        "description": "深度工程架构与 Clean Code 专家",
        "icon": "Code2",
        "is_default": False,
    },
    {
        "id": "deep_reasoner",
        "name": "深度思考",
        "description": "逐步严密推导、数学证明与逻辑分析",
        "icon": "Brain",
        "is_default": False,
    },
    {
        "id": "direct_chat",
        "name": "直接对话",
        "description": "极速响应、简洁自然语言问答",
        "icon": "MessageSquare",
        "is_default": False,
    },
]


def get_registered_agents() -> list[dict[str, Any]]:
    """获取所有已注册的智能体元数据列表."""
    return list(AGENT_REGISTRY)


def resolve_agent_intent(query: str, preference: str) -> str:
    """解析智能体路由意图.

    Args:
        query: 用户的最新输入文本
        preference: 偏好设置 (auto / direct_chat / code_assistant / deep_reasoner)

    Returns:
        str: 确定的 Agent 标识
    """
    if preference and preference != "auto":
        return preference

    # 自动识别意图规则
    lower_query = query.lower()
    code_keywords = {
        "python",
        "code",
        "function",
        "class",
        "bug",
        "def ",
        "import ",
        "sql",
        "error",
        "api",
    }
    if any(kw in lower_query for kw in code_keywords):
        return "code_assistant"

    reasoning_keywords = {
        "why",
        "prove",
        "math",
        "derive",
        "analyze",
        "calculate",
        "为什么",
        "推导",
        "证明",
    }
    if any(kw in lower_query for kw in reasoning_keywords):
        return "deep_reasoner"

    return "direct_chat"


def router_node(state: AgentState) -> dict[str, Any]:
    """意图识别与提示词装配节点."""
    messages = state.get("messages", [])
    preference = state.get("agent_preference", "auto")

    # 提取最后一条用户输入作为意图分析输入
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break

    resolved_agent = resolve_agent_intent(last_user_msg, preference)
    logger.debug(
        f"Router resolved agent: {resolved_agent} for user_msg='{last_user_msg[:30]}'"
    )

    # 装配系统提示词
    base_prompt = AGENT_PROMPTS.get(resolved_agent, AGENT_PROMPTS["direct_chat"])
    custom_prompt = state.get("system_prompt")
    if custom_prompt:
        system_content = f"{base_prompt}\n\nAdditional instructions:\n{custom_prompt}"
    else:
        system_content = base_prompt

    # 构造含 system 提示词的完整上下文
    prepared_messages: list[dict[str, str]] = [
        {"role": "system", "content": system_content}
    ]
    for m in messages:
        if m.get("role") != "system":
            prepared_messages.append({"role": m["role"], "content": m["content"]})

    return {
        "resolved_agent": resolved_agent,
        "messages": prepared_messages,
    }


async def llm_node(state: AgentState) -> dict[str, Any]:
    """LLM 统一调用节点 (非流式完整执行)."""
    messages = state.get("messages", [])
    model = state.get("model", "deepseek-v4-flash")

    client: LiteLLMClient = get_litellm_client()
    resp = await client.acompletion(messages=messages, model=model)

    return {
        "final_response": resp["content"],
        "metadata": {"usage": resp.get("usage", {})},
    }


def build_chat_workflow() -> Any:
    """构建 LangGraph 状态图工作流.

    Returns:
        CompiledStateGraph: 编译后的 LangGraph 工作流
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("router", router_node)
    workflow.add_node("llm", llm_node)

    workflow.set_entry_point("router")
    workflow.add_edge("router", "llm")
    workflow.add_edge("llm", END)

    return workflow.compile()


async def astream_chat(
    messages: list[dict[str, str]],
    model: str,
    agent_preference: str = "auto",
    system_prompt: str | None = None,
    stop_checker: Callable[[], bool | Any] | None = None,
    litellm_client: LiteLLMClient | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """智能体流式推理统一入口 (支持实时中断与 Agent 标签附着).

    Args:
        messages: 上下文消息列表
        model: 模型名称
        agent_preference: 智能体偏好 (auto 等)
        system_prompt: 自定义提示词
        stop_checker: 可调用的中断检查函数 (返回 True 则立即中断流)
        litellm_client: 可选 LiteLLM 客户端依赖注入 (用于测试 mock)

    Yields:
        dict: 包含增量 delta, finish_reason, model, agent 的字典
    """
    client = litellm_client or get_litellm_client()

    # 执行路由节点逻辑
    init_state: AgentState = {
        "messages": messages,
        "model": model,
        "agent_preference": agent_preference,
        "system_prompt": system_prompt,
    }
    routed = router_node(init_state)
    resolved_agent = routed["resolved_agent"]
    prepared_messages = routed["messages"]

    logger.debug(f"astream_chat start: agent={resolved_agent}, model={model}")

    # 调用 LiteLLM 流式输出
    stream = client.astream_completion(messages=prepared_messages, model=model)

    async for chunk in stream:
        # 实时检查外部中断信号 (如前端点击停止生成)
        if stop_checker:
            is_stopped = stop_checker()
            if hasattr(is_stopped, "__await__"):
                is_stopped = await is_stopped

            if is_stopped:
                logger.info("Chat generation stopped by external signal")
                yield {
                    "delta": "",
                    "finish_reason": "stop",
                    "model": model,
                    "agent": resolved_agent,
                }
                break

        yield {
            "delta": chunk.get("delta", ""),
            "finish_reason": chunk.get("finish_reason"),
            "model": chunk.get("model", model),
            "agent": resolved_agent,
            "tool_progress": chunk.get("tool_progress"),
        }
