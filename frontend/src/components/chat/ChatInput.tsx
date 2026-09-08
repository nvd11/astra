import React, { useRef, useEffect } from 'react';
import {
  ArrowUp,
  Square,
  Paperclip,
} from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { AVAILABLE_AGENTS, AVAILABLE_MODELS } from '@/types';
import { AgentSelector } from './AgentSelector';
import { ModelSelector } from './ModelSelector';

interface ChatInputProps {
  onSendMessage?: (content: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage }) => {
  const {
    inputPrompt,
    setInputPrompt,
    currentModel,
    currentAgent,
    isStreaming,
    setIsStreaming,
  } = useChatStore();

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动根据输入内容伸缩高度 (最大 200px)
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputPrompt]);

  const handleSend = () => {
    if (!inputPrompt.trim() || isStreaming) return;
    const text = inputPrompt.trim();
    if (onSendMessage) {
      onSendMessage(text);
    }
    setInputPrompt('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleStop = () => {
    setIsStreaming(false);
  };

  const activeAgent = AVAILABLE_AGENTS.find((a) => a.id === currentAgent) || AVAILABLE_AGENTS[0];
  const activeModel = AVAILABLE_MODELS.find((m) => m.id === currentModel) || AVAILABLE_MODELS[0];

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4 select-none">
      {/* 悬浮输入卡片 */}
      <div className="relative rounded-2xl border border-zinc-200/90 dark:border-zinc-800 bg-white dark:bg-zinc-900/90 shadow-md hover:shadow-lg dark:shadow-2xl transition-all focus-within:border-zinc-400 dark:focus-within:border-zinc-600">
        {/* 上方胶囊选择器工具条 (不可使用 overflow-x-auto，避免裁切向上弹出的悬浮菜单) */}
        <div className="px-3 pt-2.5 pb-1.5 flex items-center gap-2 border-b border-zinc-100 dark:border-zinc-800/50 relative z-20">
          <AgentSelector />
          <ModelSelector />
        </div>

        {/* 核心多行输入区域 */}
        <div className="px-3.5 py-2.5 flex items-end gap-2">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`向 ${activeAgent.name} 提问，基于 ${activeModel.name}... (Shift+Enter 换行)`}
            className="flex-1 max-h-48 resize-none bg-transparent text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none leading-relaxed py-1"
          />

          {/* 附件与发送控制按钮 */}
          <div className="flex items-center gap-1.5 pb-0.5">
            <button
              type="button"
              className="p-1.5 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 rounded-lg transition-colors"
              title="上传文档/切片文件 (支持 RAG 知识库)"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            {isStreaming ? (
              <button
                type="button"
                onClick={handleStop}
                className="w-8 h-8 rounded-xl bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-all shadow-sm active:scale-95 animate-pulse"
                title="停止生成"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSend}
                disabled={!inputPrompt.trim()}
                className="w-8 h-8 rounded-xl bg-zinc-900 dark:bg-white disabled:bg-zinc-200 dark:disabled:bg-zinc-800 text-white dark:text-zinc-900 disabled:text-zinc-400 dark:disabled:text-zinc-600 flex items-center justify-center transition-all shadow-sm active:scale-95 disabled:cursor-not-allowed"
                title="发送消息 (Enter)"
              >
                <ArrowUp className="w-4 h-4 stroke-[2.5]" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 底部合规声明提示 */}
      <p className="text-[11px] text-zinc-400 dark:text-zinc-500 text-center mt-2">
        Astra 可能会生成不准确的信息，请核实重要财务与代码细节。
      </p>
    </div>
  );
};
