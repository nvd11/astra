import { create } from 'zustand';
import { Conversation, Message, AgentType } from '@/types';

interface ChatStore {
  // 会话与消息列表
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Message[];

  // 偏好与模型状态
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
}

export const useChatStore = create<ChatStore>((set) => ({
  conversations: [
    {
      id: 'demo-1',
      session_id: 'session-sample-1',
      title: 'Python 异步微服务架构讨论',
      model: 'deepseek-v4-flash',
      agent_preference: 'code_assistant',
      system_prompt: null,
      is_archived: false,
      created_at: new Date(Date.now() - 3600000).toISOString(),
      updated_at: new Date(Date.now() - 1800000).toISOString(),
      message_count: 6,
    },
    {
      id: 'demo-2',
      session_id: 'session-sample-2',
      title: '傅里叶变换公式严密推导',
      model: 'gemini-3.8-flash',
      agent_preference: 'deep_reasoner',
      system_prompt: null,
      is_archived: false,
      created_at: new Date(Date.now() - 86400000).toISOString(),
      updated_at: new Date(Date.now() - 82800000).toISOString(),
      message_count: 4,
    },
  ],
  activeConversationId: null,
  messages: [],
  currentModel: 'deepseek-v4-flash',
  currentAgent: 'auto',
  inputPrompt: '',
  isStreaming: false,

  isSidebarOpen: true,
  isMobileDrawerOpen: false,

  setConversations: (conversations) => set({ conversations }),
  setActiveConversationId: (id) => set({ activeConversationId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setCurrentModel: (currentModel) => set({ currentModel }),
  setCurrentAgent: (currentAgent) => set({ currentAgent }),
  setInputPrompt: (inputPrompt) => set({ inputPrompt }),
  setIsStreaming: (isStreaming) => set({ isStreaming }),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSidebarOpen: (isSidebarOpen) => set({ isSidebarOpen }),
  toggleMobileDrawer: () => set((state) => ({ isMobileDrawerOpen: !state.isMobileDrawerOpen })),
  setMobileDrawerOpen: (isMobileDrawerOpen) => set({ isMobileDrawerOpen }),

  startNewChat: () =>
    set({
      activeConversationId: null,
      messages: [],
      inputPrompt: '',
      isMobileDrawerOpen: false,
    }),
}));
