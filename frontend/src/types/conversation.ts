import { AgentType } from './agent';

/**
 * 会话元数据 (与后端 ConversationData 严格对齐)
 */
export interface Conversation {
  id: string;
  session_id: string | null;
  title: string;
  model: string;
  agent_preference: AgentType | string;
  system_prompt: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
}
