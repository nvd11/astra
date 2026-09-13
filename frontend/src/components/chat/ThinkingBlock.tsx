import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Brain, Sparkles } from 'lucide-react';

interface ThinkingBlockProps {
  thinking: string;
  isStreaming?: boolean;
}

export const ThinkingBlock: React.FC<ThinkingBlockProps> = ({ thinking, isStreaming }) => {
  // 流式中默认展开让用户实时看到推理，流式结束后可折叠以防占据过多篇幅
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  if (!thinking || !thinking.trim()) return null;

  const charCount = thinking.length;

  return (
    <div className="my-2 rounded-xl border border-indigo-200/60 dark:border-indigo-900/40 bg-indigo-50/40 dark:bg-indigo-950/20 backdrop-blur-xs overflow-hidden transition-all text-xs">
      {/* 头部折叠控制条 */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between text-left hover:bg-indigo-100/40 dark:hover:bg-indigo-900/30 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0 pr-2">
          {isStreaming ? (
            <div className="relative flex items-center justify-center">
              <Brain className="w-4 h-4 text-indigo-500 animate-pulse" />
              <span className="absolute -top-1 -right-1 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
              </span>
            </div>
          ) : (
            <Sparkles className="w-3.5 h-3.5 text-indigo-400 dark:text-indigo-300 shrink-0" />
          )}

          <div className="flex items-center gap-1.5 truncate font-medium text-indigo-700 dark:text-indigo-300">
            <span>{isStreaming ? '正在深度思考推演中...' : '已完成思考推演'}</span>
            <span className="text-[11px] text-indigo-400 dark:text-indigo-400 font-normal">
              ({charCount} 字)
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1 text-[11px] text-indigo-400 dark:text-indigo-400 shrink-0">
          <span>{isExpanded ? '收起' : '展开'}</span>
          {isExpanded ? (
            <ChevronDown className="w-3.5 h-3.5" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5" />
          )}
        </div>
      </button>

      {/* 思考内容主体 */}
      {isExpanded && (
        <div className="px-3.5 pb-3 pt-1 border-t border-indigo-100/80 dark:border-indigo-900/30 text-zinc-600 dark:text-zinc-400 font-mono text-[11px] leading-relaxed whitespace-pre-wrap break-words select-text">
          {thinking}
          {isStreaming && (
            <span className="inline-block w-1.5 h-3.5 ml-1 bg-indigo-500 rounded-xs animate-pulse align-middle" />
          )}
        </div>
      )}
    </div>
  );
};
