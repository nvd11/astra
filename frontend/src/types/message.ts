export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

/**
 * 消息明细实体 (与后端 MessageData 严格对齐)
 */
export interface Message {
  id: string;
  conversation_id: string;
  session_id: string | null;
  role: MessageRole;
  content: string;
  metadata?: {
    agent?: string;
    finish_reason?: string | null;
    tokens_used?: number;
    thinking?: string;
  } | null;
  tokens_used?: number | null;
  created_at: string;
  isStreaming?: boolean;
}

/**
 * SSE 流式数据帧 (与后端 ChatStreamChunkData 对齐)
 */
export interface ChatStreamChunk {
  id: string;
  delta: string;
  finish_reason: string | null;
  model: string;
  agent: string;
}
