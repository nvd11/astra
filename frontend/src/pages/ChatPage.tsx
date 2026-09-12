import React, { useRef, useState } from 'react';
import { Sparkles, User as UserIcon, ArrowDown, Cpu, Loader2 } from 'lucide-react';
import { EmptyState } from '@/components/chat/EmptyState';
import { ChatInput } from '@/components/chat/ChatInput';
import { MarkdownRenderer } from '@/components/chat/MarkdownRenderer';
import { ToolProgressCard } from '@/components/chat/ToolProgressCard';
import { useChatStore } from '@/stores/chatStore';
import { useTypewriter } from '@/hooks/useTypewriter';
import { useAutoScroll } from '@/hooks/useAutoScroll';
import { chatService } from '@/services/chat';
import { Message, ToolProgressEvent } from '@/types';
import { storage } from '@/utils/storage';

export const ChatPage: React.FC = () => {
  const {
    messages,
    addMessage,
    updateMessage,
    activeConversationId,
    setActiveConversationId,
    conversations,
    setConversations,
    currentModel,
    currentAgent,
    isStreaming,
    setIsStreaming,
    setAbortController,
    isLoadingMessages,
  } = useChatStore();

  const [streamingToolEvents, setStreamingToolEvents] = useState<ToolProgressEvent[]>([]);
  const activeAssistantMsgIdRef = useRef<string | null>(null);

  // 1. 智能吸底与用户脱钩滚动 Hook
  const { scrollRef, showScrollButton, scrollToBottom, autoScrollIfAttached } =
    useAutoScroll({ threshold: 60 });

  // 2. 60 FPS RAF 动态自适应字符缓冲池打字机 Hook
  const typewriter = useTypewriter({
    onComplete: (fullText) => {
      const msgId = activeAssistantMsgIdRef.current;
      if (msgId) {
        updateMessage(msgId, {
          content: fullText,
          isStreaming: false,
          metadata: {
            tool_progresses: streamingToolEvents,
          },
        });
      }
      setIsStreaming(false);
      setAbortController(null);
      activeAssistantMsgIdRef.current = null;
      // 结束后最终吸底对齐
      autoScrollIfAttached();
    },
  });

  // 当打字机输出新文本字符时，驱动吸底
  React.useEffect(() => {
    if (typewriter.displayedText) {
      autoScrollIfAttached();
    }
  }, [typewriter.displayedText, autoScrollIfAttached]);

  // 发送消息核心驱动流
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isStreaming) return;

    let convId = activeConversationId;

    // 1. 若当前处于未选择会话的空白态，先自动调用后端创建会话
    if (!convId) {
      const titleCandidate =
        text.length > 20 ? `${text.slice(0, 20)}...` : text;
      try {
        const newConv = await chatService.createConversation({
          title: titleCandidate,
          model: currentModel,
          agent_preference: currentAgent,
        });
        convId = newConv.id;
        setActiveConversationId(convId);
        setConversations([newConv, ...conversations]);
      } catch (e: unknown) {
        console.error('Failed to create conversation:', e);
        const errMsg = e instanceof Error ? e.message : String(e);
        typewriter.enqueue(`*(创建会话失败: ${errMsg})*`);
        typewriter.flush();
        setIsStreaming(false);
        return;
      }
    }

    // 2. 构造用户提问消息并立即呈现
    const userMsgId = `user-${Date.now()}`;
    const userMsg: Message = {
      id: userMsgId,
      conversation_id: convId,
      session_id: storage.getSessionId(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    addMessage(userMsg);

    // 3. 构造 Assistant 占位消息
    const assistantMsgId = `assistant-${Date.now()}`;
    activeAssistantMsgIdRef.current = assistantMsgId;

    const placeholderAssistantMsg: Message = {
      id: assistantMsgId,
      conversation_id: convId,
      session_id: storage.getSessionId(),
      role: 'assistant',
      content: '',
      isStreaming: true,
      metadata: {
        agent: currentAgent,
      },
      created_at: new Date().toISOString(),
    };
    addMessage(placeholderAssistantMsg);

    // 4. 重置打字机并开启流状态
    setStreamingToolEvents([]);
    typewriter.reset();
    setIsStreaming(true);

    const abortController = new AbortController();
    setAbortController(abortController);

    // 立即向底部滚动一次
    scrollToBottom(true);

    // 5. 调用后端真实 SSE 流式推理接口
    await chatService.streamChat({
      conversationId: convId,
      content: text,
      modelOverride: currentModel,
      agentOverride: currentAgent,
      signal: abortController.signal,
      onToolProgress: (event) => {
        setStreamingToolEvents((prev) => {
          const existingIdx = prev.findIndex((e) => e.toolCallId === event.toolCallId && event.toolCallId);
          if (existingIdx >= 0) {
            const next = [...prev];
            next[existingIdx] = { ...next[existingIdx], ...event };
            return next;
          }
          return [...prev, event];
        });
        autoScrollIfAttached();
      },
      onDelta: (delta, chunk) => {
        typewriter.enqueue(delta);
        if (chunk?.agent) {
          updateMessage(assistantMsgId, {
            metadata: { agent: chunk.agent },
          });
        }
      },
      onFinish: () => {
        typewriter.endStream();
      },
      onError: (err) => {
        console.error('Chat stream error:', err);
        typewriter.enqueue(`\n\n*(请求发生异常: ${err.message})*`);
        typewriter.flush();
      },
    });
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-zinc-50/50 dark:bg-zinc-950 relative">
      {/* 消息滚动流容器 (绑定 autoScroll ref) */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
        {isLoadingMessages ? (
          <div className="flex items-center justify-center gap-2 py-16 text-xs text-zinc-400">
            <Loader2 className="w-4 h-4 animate-spin text-sky-500" />
            <span>正在加载历史对话记录...</span>
          </div>
        ) : messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="max-w-4xl xl:max-w-5xl mx-auto space-y-6">
            {messages.map((msg) => {
              const isCurrentStreamingMsg =
                msg.id === activeAssistantMsgIdRef.current;
              const contentToDisplay = isCurrentStreamingMsg
                ? typewriter.displayedText
                : msg.content;

              return (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 sm:gap-4 ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start w-full'
                  } animate-in fade-in duration-200`}
                >
                  {/* Assistant 头像 */}
                  {msg.role !== 'user' && (
                    <div className="w-8 h-8 rounded-xl bg-sky-500 flex items-center justify-center text-white flex-shrink-0 mt-1 shadow-sm shadow-sky-500/20">
                      <Sparkles className="w-4 h-4 fill-current" />
                    </div>
                  )}

                  {/* 消息主体容器 (AI 回复充分舒展占据全宽) */}
                  <div
                    className={
                      msg.role === 'user'
                        ? 'max-w-[88%] sm:max-w-[75%] space-y-1.5'
                        : 'flex-1 min-w-0 space-y-1.5'
                    }
                  >
                    {/* 消息元数据标签 (Agent / Model) */}
                    {msg.role !== 'user' && msg.metadata?.agent && (
                      <div className="flex items-center gap-1.5 text-[11px] text-zinc-400 font-medium pl-1">
                        <Cpu className="w-3.5 h-3.5" />
                        <span>{msg.metadata.agent}</span>
                      </div>
                    )}

                    <div
                      className={`rounded-2xl px-5 py-4 text-sm leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 rounded-br-sm shadow-sm'
                          : 'bg-white text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200 rounded-bl-sm border border-zinc-200/80 dark:border-zinc-800 shadow-xs'
                      }`}
                    >
                      {msg.role === 'user' ? (
                        <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                      ) : (
                        <div className="w-full">
                          {/* 🎯 工具调用进度指示卡片 (实时流中或历史落库消息) */}
                          {isCurrentStreamingMsg && streamingToolEvents.length > 0 && (
                            <ToolProgressCard events={streamingToolEvents} />
                          )}
                          {!isCurrentStreamingMsg && msg.metadata?.tool_progresses && msg.metadata.tool_progresses.length > 0 && (
                            <ToolProgressCard events={msg.metadata.tool_progresses} />
                          )}

                          <MarkdownRenderer content={contentToDisplay} />
                          {/* 呼吸脉冲打字光标 */}
                          {isCurrentStreamingMsg && typewriter.isTyping && (
                            <span className="inline-block w-1.5 h-4 ml-1 bg-sky-500 rounded-xs animate-pulse align-middle" />
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* User 头像 */}
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-xl bg-zinc-200 dark:bg-zinc-800 flex items-center justify-center text-zinc-700 dark:text-zinc-300 flex-shrink-0 mt-1">
                      <UserIcon className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 用户向上翻阅时的悬浮“回到最新内容”按钮 */}
      {showScrollButton && (
        <button
          onClick={() => scrollToBottom(true)}
          className="absolute bottom-24 right-8 z-30 flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-white dark:bg-zinc-800 shadow-lg border border-zinc-200 dark:border-zinc-700 text-xs font-medium text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-all active:scale-95 animate-in fade-in"
          title="滚动到底部最新消息"
        >
          <ArrowDown className="w-3.5 h-3.5 text-sky-500" />
          <span>回到最新内容</span>
        </button>
      )}

      {/* 底部固定输入坞 */}
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
};
