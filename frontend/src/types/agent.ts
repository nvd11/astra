/**
 * 智能体枚举与显示配置
 */
export type AgentType = 'auto' | 'code_assistant' | 'deep_reasoner' | 'direct_chat';

export interface AgentInfo {
  id: AgentType;
  name: string;
  description: string;
  icon: string;
}

export const AVAILABLE_AGENTS: AgentInfo[] = [
  {
    id: 'auto',
    name: '自动路由',
    description: 'Main Agent 根据提问智能意图分发',
    icon: 'Sparkles',
  },
  {
    id: 'code_assistant',
    name: '代码助手',
    description: '深度工程架构与 Clean Code 专家',
    icon: 'Code2',
  },
  {
    id: 'deep_reasoner',
    name: '深度思考',
    description: '逐步严密推导、数学证明与逻辑分析',
    icon: 'Brain',
  },
  {
    id: 'direct_chat',
    name: '直接对话',
    description: '极速响应、简洁自然语言问答',
    icon: 'MessageSquare',
  },
];

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
