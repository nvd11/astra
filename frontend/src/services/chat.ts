import axios from 'axios';
import {
  AgentInfo,
  BaseResponse,
  ChatStreamChunk,
  Conversation,
  ModelInfo,
} from '@/types';
import { storage } from '@/utils/storage';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/astra/api';

export interface StreamChatParams {
  conversationId: string;
  content: string;
  modelOverride?: string;
  agentOverride?: string;
  signal?: AbortSignal;
  onDelta: (delta: string, chunk?: ChatStreamChunk) => void;
  onFinish: () => void;
  onError: (err: Error) => void;
}

export const chatService = {
  /**
   * 动态拉取 LiteLLM 网关真实配准的可用模型列表 (零 Hardcode)
   */
  async getModels(): Promise<ModelInfo[]> {
    try {
      const response = await axios.get<BaseResponse<ModelInfo[]>>(
        `${API_BASE_URL}/chat/models`
      );
      if (
        response.data &&
        response.data.code === 0 &&
        Array.isArray(response.data.data)
      ) {
        return response.data.data;
      }
      return [];
    } catch (err) {
      console.warn('Failed to fetch models dynamically from API:', err);
      return [];
    }
  },

  /**
   * 动态拉取后端 LangGraph 注册支持的智能体清单 (零 Hardcode)
   */
  async getAgents(): Promise<AgentInfo[]> {
    try {
      const response = await axios.get<BaseResponse<AgentInfo[]>>(
        `${API_BASE_URL}/chat/agents`
      );
      if (
        response.data &&
        response.data.code === 0 &&
        Array.isArray(response.data.data)
      ) {
        return response.data.data;
      }
      return [];
    } catch (err) {
      console.warn('Failed to fetch agents dynamically from API:', err);
      return [];
    }
  },

  /**
   * 创建新会话 (支持 X-Session-ID 设备会话审计)
   */
  async createConversation(data: {
    title: string;
    model?: string;
    agent_preference?: string;
  }): Promise<Conversation> {
    const sessionId = storage.getSessionId();
    const token = storage.getToken();

    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      if (sessionId) {
        headers['X-Session-ID'] = sessionId;
      }
    }

    const response = await axios.post<BaseResponse<Conversation>>(
      `${API_BASE_URL}/conversations`,
      data,
      { headers }
    );
    return response.data.data;
  },

  /**
   * 原生 Fetch SSE 流式消费 (协议逐帧解析 + 审计溯源注入 + Abort 支持)
   */
  async streamChat(params: StreamChatParams): Promise<void> {
    const {
      conversationId,
      content,
      modelOverride,
      agentOverride,
      signal,
      onDelta,
      onFinish,
      onError,
    } = params;

    const sessionId = storage.getSessionId();
    const token = storage.getToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      if (sessionId) {
        headers['X-Session-ID'] = sessionId;
      }
    }

    const bodyPayload = {
      conversation_id: conversationId,
      content: content,
      model_override: modelOverride,
      agent_override: agentOverride,
      stream: true,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(bodyPayload),
        signal,
      });

      if (!response.ok) {
        throw new Error(
          `Chat stream request failed with HTTP ${response.status}`
        );
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported by response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;

          const dataStr = trimmed.replace(/^data:\s*/, '');
          if (dataStr === '[DONE]') {
            onFinish();
            return;
          }

          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.error) {
              throw new Error(parsed.message || 'Stream generation error');
            }
            if (parsed.delta) {
              onDelta(parsed.delta, parsed as ChatStreamChunk);
            }
            if (parsed.finish_reason) {
              onFinish();
              return;
            }
          } catch (e) {
            // 非 JSON 格式或截断字符静默跳过
          }
        }
      }

      onFinish();
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        // 用户主动停止推理，正常结束
        onFinish();
      } else {
        onError(err instanceof Error ? err : new Error(String(err)));
      }
    }
  },

  /**
   * 手动中止当前进行中的推理
   */
  async stopChat(conversationId: string): Promise<void> {
    try {
      await axios.post(`${API_BASE_URL}/chat/stop`, {
        conversation_id: conversationId,
      });
    } catch (err) {
      console.warn('Failed to send stop signal to backend:', err);
    }
  },
};
