"""智能体状态定义模块 (LangGraph Agent State)."""

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """LangGraph 智能体全局图执行状态."""

    messages: list[dict[str, str]]
    model: str
    agent_preference: str
    system_prompt: str | None
    conversation_id: str
    user_id: str
    resolved_agent: str
    final_response: str
    metadata: dict[str, Any]
