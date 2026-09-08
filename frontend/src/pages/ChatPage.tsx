import React, { useState } from 'react';
import { EmptyState } from '@/components/chat/EmptyState';
import { ChatInput } from '@/components/chat/ChatInput';
import { useChatStore } from '@/stores/chatStore';
import { Message } from '@/types';
import { Sparkles, User as UserIcon } from 'lucide-react';

export const ChatPage: React.FC = () => {
  const {
    messages,
    addMessage,
    currentModel,
    currentAgent,
    setIsStreaming,
  } = useChatStore();

  const [localMessages, setLocalMessages] = useState<Message[]>(messages);

  const handleSendMessage = (text: string) => {
    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      conversation_id: 'conv-active',
      session_id: 'session-client',
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    const newMsgs = [...localMessages, userMsg];
    setLocalMessages(newMsgs);
    addMessage(userMsg);

    // 模拟流式打字机打底响应
    setIsStreaming(true);
    setTimeout(() => {
      const assistantMsg: Message = {
        id: `msg-ai-${Date.now()}`,
        conversation_id: 'conv-active',
        session_id: 'session-client',
        role: 'assistant',
        content: `你好！我是 Astra。我已经收到您的需求：“${text}”。\n\n当前已自动调度 **${currentAgent}** 智能体，并使用 **${currentModel}** 模型引擎为您处理。全套 Markdown、KaTeX 公式与 Artifacts 代码沙箱功能均已就绪！`,
        metadata: {
          agent: currentAgent,
        },
        created_at: new Date().toISOString(),
      };
      setLocalMessages((prev) => [...prev, assistantMsg]);
      addMessage(assistantMsg);
      setIsStreaming(false);
    }, 800);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-white dark:bg-zinc-950">
      {/* 消息滚动流 */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {localMessages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="max-w-3xl mx-auto space-y-6">
            {localMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3.5 ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.role !== 'user' && (
                  <div className="w-7 h-7 rounded-lg bg-sky-500 flex items-center justify-center text-white flex-shrink-0 mt-0.5 shadow-sm">
                    <Sparkles className="w-4 h-4 fill-current" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-br-sm'
                      : 'bg-zinc-100 dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 rounded-bl-sm border border-zinc-200/50 dark:border-zinc-800'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>

                {msg.role === 'user' && (
                  <div className="w-7 h-7 rounded-lg bg-zinc-300 dark:bg-zinc-700 flex items-center justify-center text-zinc-700 dark:text-zinc-200 flex-shrink-0 mt-0.5">
                    <UserIcon className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 底部固定输入坞 */}
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
};
