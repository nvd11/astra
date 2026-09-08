import axios from 'axios';
import { AgentInfo, BaseResponse, ModelInfo } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/astra/api';

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
};
