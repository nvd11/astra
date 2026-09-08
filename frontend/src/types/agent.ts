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
 * 支持的底层 LLM 模型列表
 */
export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description: string;
}

export const AVAILABLE_MODELS: ModelInfo[] = [
  {
    id: 'deepseek-v4-flash',
    name: 'DeepSeek V4 Flash',
    provider: 'DeepSeek',
    description: '极速代码与推理，日常高频首选',
  },
  {
    id: 'gemini-3.8-flash',
    name: 'Gemini 3.8 Flash',
    provider: 'Google',
    description: '低延迟、多模态超强推理',
  },
  {
    id: 'claude-sonnet-4-6',
    name: 'Claude Sonnet 4.6',
    provider: 'Anthropic',
    description: '长文本架构与严谨工程分析',
  },
  {
    id: 'qwen-max',
    name: 'Qwen Max',
    provider: 'Alibaba',
    description: '中文语境精深理解与创作',
  },
];
