import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Code2,
  Brain,
  MessageSquare,
  ChevronDown,
  Check,
} from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { AVAILABLE_AGENTS, AgentType } from '@/types';
import { cn } from '@/utils/cn';

const AGENT_ICON_MAP = {
  Sparkles,
  Code2,
  Brain,
  MessageSquare,
};

export const AgentSelector: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const { currentAgent, setCurrentAgent } = useChatStore();

  const activeAgent =
    AVAILABLE_AGENTS.find((a) => a.id === currentAgent) || AVAILABLE_AGENTS[0];
  const ActiveIcon =
    AGENT_ICON_MAP[activeAgent.icon as keyof typeof AGENT_ICON_MAP] || Sparkles;

  // 点击外部自动收起
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleSelect = (agentId: AgentType) => {
    setCurrentAgent(agentId);
    setIsOpen(false);
  };

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      {/* 胶囊触发按钮 */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full transition-all border shadow-2xs select-none',
          isOpen
            ? 'bg-zinc-200/90 dark:bg-zinc-700 text-zinc-900 dark:text-white border-zinc-300 dark:border-zinc-600'
            : 'bg-zinc-100/90 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200/80 dark:hover:bg-zinc-700 border-zinc-200/70 dark:border-zinc-700/60'
        )}
      >
        <ActiveIcon className="w-3.5 h-3.5 text-sky-500 flex-shrink-0" />
        <span>{activeAgent.name}</span>
        <ChevronDown
          className={cn(
            'w-3 h-3 text-zinc-400 transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {/* 悬浮 Popover 菜单 */}
      {isOpen && (
        <div className="absolute left-0 bottom-full mb-2 w-64 rounded-2xl border border-zinc-200/90 dark:border-zinc-800 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md shadow-xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-150">
          <div className="px-2.5 py-1 text-[10px] font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider">
            智能体路由偏好
          </div>

          <div className="space-y-0.5 mt-1">
            {AVAILABLE_AGENTS.map((agent) => {
              const isSelected = agent.id === currentAgent;
              const Icon =
                AGENT_ICON_MAP[agent.icon as keyof typeof AGENT_ICON_MAP] ||
                Sparkles;

              return (
                <div
                  key={agent.id}
                  onClick={() => handleSelect(agent.id)}
                  className={cn(
                    'flex items-center justify-between px-2.5 py-2 rounded-xl text-xs cursor-pointer transition-all',
                    isSelected
                      ? 'bg-sky-50 dark:bg-sky-950/40 text-sky-950 dark:text-sky-200 font-medium'
                      : 'text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100/80 dark:hover:bg-zinc-800/60'
                  )}
                >
                  <div className="flex items-center gap-2.5 truncate pr-2">
                    <div
                      className={cn(
                        'w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0',
                        isSelected
                          ? 'bg-sky-500 text-white'
                          : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400'
                      )}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </div>

                    <div className="truncate">
                      <div className="text-xs truncate">{agent.name}</div>
                      <div className="text-[10px] text-zinc-400 dark:text-zinc-500 truncate mt-0.5 font-normal">
                        {agent.description}
                      </div>
                    </div>
                  </div>

                  {isSelected && (
                    <Check className="w-4 h-4 text-sky-500 flex-shrink-0" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
