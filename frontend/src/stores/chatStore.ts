import { create } from 'zustand';
import { Conversation, Message, AgentType, ModelInfo } from '@/types';
import { chatService } from '@/services/chat';

interface ChatStore {
  // 会话与消息列表
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Message[];

  // 动态模型发现列表 (由 LiteLLM 网关实时同步，严禁 Hardcode)
  availableModels: ModelInfo[];
  isLoadingModels: boolean;

  // 偏好与当前模型状态
  currentModel: string;
  currentAgent: AgentType;
  inputPrompt: string;
  isStreaming: boolean;

  // 响应式布局状态
  isSidebarOpen: boolean; // PC 端侧边栏展开/折叠
  isMobileDrawerOpen: boolean; // 移动端侧滑抽屉展开/折叠

  // 操作函数
  setConversations: (conversations: Conversation[]) => void;
  setActiveConversationId: (id: string | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  setCurrentModel: (model: string) => void;
  setCurrentAgent: (agent: AgentType) => void;
  setInputPrompt: (prompt: string) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleMobileDrawer: () => void;
  setMobileDrawerOpen: (open: boolean) => void;
  startNewChat: () => void;
  fetchModels: () => Promise<void>;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],

  // 动态模型初始列表
  availableModels: [],
  isLoadingModels: false,

  currentModel: 'gemini-3.8-flash',
  currentAgent: 'auto',
  inputPrompt: '',
  isStreaming: false,

  isSidebarOpen: true,
  isMobileDrawerOpen: false,

  fetchModels: async () => {
    set({ isLoadingModels: true });
    const models = await chatService.getModels();
    if (models.length > 0) {
      const defaultModel = models.find((m) => m.is_default) || models[0];
      const state = get();
      const currentStillValid = models.some((m) => m.id === state.currentModel);

      set({
        availableModels: models,
        currentModel: currentStillValid ? state.currentModel : defaultModel.id,
        isLoadingModels: false,
      });
    } else {
      set({ isLoadingModels: false });
    }
  },

  setConversations: (conversations) => set({ conversations }),
  setActiveConversationId: (id) =>
    set((state) => {
      if (!id) {
        return { activeConversationId: null };
      }
      const conv = state.conversations.find((c) => c.id === id);
      if (conv) {
        return {
          activeConversationId: id,
          currentModel: conv.model || state.currentModel,
          currentAgent: (conv.agent_preference as AgentType) || state.currentAgent,
        };
      }
      return { activeConversationId: id };
    }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setCurrentModel: (model) =>
    set((state) => ({
      currentModel: model,
      conversations: state.activeConversationId
        ? state.conversations.map((c) =>
            c.id === state.activeConversationId ? { ...c, model } : c
          )
        : state.conversations,
    })),
  setCurrentAgent: (agent) =>
    set((state) => ({
      currentAgent: agent,
      conversations: state.activeConversationId
        ? state.conversations.map((c) =>
            c.id === state.activeConversationId
              ? { ...c, agent_preference: agent }
              : c
          )
        : state.conversations,
    })),
  setInputPrompt: (inputPrompt) => set({ inputPrompt }),
  setIsStreaming: (isStreaming) => set({ isStreaming }),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSidebarOpen: (isSidebarOpen) => set({ isSidebarOpen }),
  toggleMobileDrawer: () =>
    set((state) => ({ isMobileDrawerOpen: !state.isMobileDrawerOpen })),
  setMobileDrawerOpen: (isMobileDrawerOpen) => set({ isMobileDrawerOpen }),

  startNewChat: () =>
    set({
      activeConversationId: null,
      messages: [],
      inputPrompt: '',
      currentModel: 'deepseek-v4-flash',
      currentAgent: 'auto',
      isMobileDrawerOpen: false,
    }),
}));
