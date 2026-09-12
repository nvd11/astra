import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Terminal, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { ToolProgressEvent } from '@/types';

interface ToolProgressCardProps {
  events: ToolProgressEvent[];
}

export const ToolProgressCard: React.FC<ToolProgressCardProps> = ({ events }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!events || events.length === 0) return null;

  // 获取最新的工具执行状态
  const activeEvent = events.find((e) => e.status === 'running') || events[events.length - 1];
  const isRunning = events.some((e) => e.status === 'running');
  const hasFailed = events.some((e) => e.status === 'failed');

  return (
    <div className="my-2 rounded-xl border border-zinc-200/80 dark:border-zinc-800/80 bg-zinc-50/70 dark:bg-zinc-900/50 backdrop-blur-xs overflow-hidden transition-all text-xs">
      {/* 头部折叠控制条 */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between text-left hover:bg-zinc-100/50 dark:hover:bg-zinc-800/40 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0 pr-2">
          {isRunning ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-500 shrink-0" />
          ) : hasFailed ? (
            <AlertCircle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
          )}

          <div className="flex items-center gap-1.5 truncate">
            {activeEvent.emoji && <span className="text-sm">{activeEvent.emoji}</span>}
            <span className="font-semibold text-zinc-700 dark:text-zinc-200 truncate">
              {isRunning ? `正在执行: ${activeEvent.tool}` : `已完成 ${events.length} 次工具调用`}
            </span>
            {activeEvent.label && isRunning && (
              <span className="text-zinc-400 dark:text-zinc-500 truncate max-w-[200px] sm:max-w-[320px]">
                ({activeEvent.label})
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] text-zinc-400 shrink-0">
          <span>{events.length} 步操作</span>
          {isExpanded ? (
            <ChevronDown className="w-3.5 h-3.5" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5" />
          )}
        </div>
      </button>

      {/* 展开查看所有工具操作详情 */}
      {isExpanded && (
        <div className="px-3.5 pb-3 pt-1 border-t border-zinc-200/40 dark:border-zinc-800/40 space-y-2">
          {events.map((evt, idx) => (
            <div
              key={evt.toolCallId || idx}
              className="flex items-start gap-2.5 py-1.5 border-b border-zinc-100 dark:border-zinc-800/30 last:border-b-0"
            >
              <div className="mt-0.5 shrink-0">
                {evt.status === 'running' ? (
                  <Loader2 className="w-3 h-3 animate-spin text-sky-500" />
                ) : evt.status === 'failed' ? (
                  <AlertCircle className="w-3 h-3 text-rose-500" />
                ) : (
                  <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                )}
              </div>

              <div className="flex-1 min-w-0 font-mono text-[11px]">
                <div className="flex items-center gap-1.5">
                  {evt.emoji && <span>{evt.emoji}</span>}
                  <span className="font-medium text-zinc-700 dark:text-zinc-300">
                    {evt.tool}
                  </span>
                  <span className="text-[10px] text-zinc-400">
                    [{evt.status}]
                  </span>
                </div>

                {evt.label && (
                  <div className="mt-1 p-2 rounded-lg bg-zinc-100/80 dark:bg-zinc-950/60 text-zinc-600 dark:text-zinc-400 break-all whitespace-pre-wrap flex items-start gap-1.5">
                    <Terminal className="w-3 h-3 text-zinc-400 shrink-0 mt-0.5" />
                    <span>{evt.label}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
