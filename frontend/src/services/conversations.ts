import {
  BaseResponse,
  Conversation,
  Message,
  PaginatedData,
} from '@/types';
import { api } from './api';

export const conversationService = {
  /**
   * 分页拉取用户的会话列表
   */
  async listConversations(
    page = 1,
    pageSize = 50,
    isArchived = false
  ): Promise<PaginatedData<Conversation>> {
    try {
      const response = await api.get<
        BaseResponse<PaginatedData<Conversation>>
      >('/conversations', {
        params: {
          page,
          page_size: pageSize,
          is_archived: isArchived,
        },
      });
      if (response.data && response.data.code === 0) {
        return response.data.data;
      }
      return { items: [], total: 0, page: 1, page_size: pageSize, has_more: false };
    } catch (err) {
      console.warn('Failed to list conversations from backend:', err);
      return { items: [], total: 0, page: 1, page_size: pageSize, has_more: false };
    }
  },

  /**
   * 获取单个会话元数据
   */
  async getConversation(id: string): Promise<Conversation | null> {
    try {
      const response = await api.get<BaseResponse<Conversation>>(
        `/conversations/${id}`
      );
      if (response.data && response.data.code === 0) {
        return response.data.data;
      }
      return null;
    } catch (err) {
      console.warn(`Failed to get conversation ${id}:`, err);
      return null;
    }
  },

  /**
   * 更新会话属性 (标题、模型、偏好)
   */
  async updateConversation(
    id: string,
    data: {
      title?: string;
      model?: string;
      agent_preference?: string;
      is_archived?: boolean;
    }
  ): Promise<Conversation | null> {
    try {
      const response = await api.put<BaseResponse<Conversation>>(
        `/conversations/${id}`,
        data
      );
      if (response.data && response.data.code === 0) {
        return response.data.data;
      }
      return null;
    } catch (err) {
      console.warn(`Failed to update conversation ${id}:`, err);
      return null;
    }
  },

  /**
   * 删除会话及其所有关联消息
   */
  async deleteConversation(id: string): Promise<boolean> {
    try {
      const response = await api.delete<BaseResponse<{ deleted: boolean }>>(
        `/conversations/${id}`
      );
      return response.data && response.data.code === 0;
    } catch (err) {
      console.warn(`Failed to delete conversation ${id}:`, err);
      return false;
    }
  },

  /**
   * 拉取指定会话下的历史消息明细 (按时间正序)
   */
  async listMessages(
    conversationId: string,
    page = 1,
    pageSize = 100
  ): Promise<Message[]> {
    try {
      const response = await api.get<BaseResponse<PaginatedData<Message>>>(
        `/conversations/${conversationId}/messages`,
        {
          params: { page, page_size: pageSize },
        }
      );
      if (response.data && response.data.code === 0 && response.data.data) {
        return response.data.data.items || [];
      }
      return [];
    } catch (err) {
      console.warn(`Failed to list messages for conv ${conversationId}:`, err);
      return [];
    }
  },
};
