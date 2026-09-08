/**
 * 智能体枚举与显示配置 (100% 由后端 /chat/agents 动态下发，严禁前端硬编码)
 */
export type AgentType = 'auto' | 'code_assistant' | 'deep_reasoner' | 'direct_chat' | string;

export interface AgentInfo {
  id: AgentType;
  name: string;
  description: string;
  icon: string;
  is_default?: boolean;
}

/**
 * 底层推理大模型元数据接口 (100% 由后端 /chat/models 动态下发，严禁前端硬编码)
 */
export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description: string;
  is_default?: boolean;
}
