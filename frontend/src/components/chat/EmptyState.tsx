import React from 'react';
import {
  Sparkles,
  Code2,
  Brain,
  ShieldCheck,
  BookOpen,
  ArrowRight,
} from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { PROMPT_SUGGESTIONS } from '@/utils/constants';

const ICON_MAP = {
  ShieldCheck,
  Code2,
  Brain,
  BookOpen,
};

export const EmptyState: React.FC = () => {
  const { setInputPrompt } = useChatStore();

  const handleSelectPrompt = (text: string) => {
    setInputPrompt(text);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center max-w-2xl mx-auto px-4 py-8 text-center select-none animate-in fade-in duration-500">
      {/* 极简发光 Logo */}
      <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-xl shadow-sky-500/20 mb-6">
        <Sparkles className="w-6 h-6 fill-current" />
      </div>

      {/* 欢迎语 */}
      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 dark:text-white mb-2">
        你好，我是 Astra。
      </h1>
      <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-8 max-w-md">
        专为严谨工程设计的企业级多智能体对话工作台。今天有什么我可以协助您的？
      </p>

      {/* 4 张灵感提示词卡片 */}
      <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
        {PROMPT_SUGGESTIONS.map((item, index) => {
          const IconComponent = ICON_MAP[item.icon as keyof typeof ICON_MAP] || Sparkles;
          return (
            <div
              key={index}
              onClick={() => handleSelectPrompt(item.prompt)}
              className="group p-4 rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 hover:border-zinc-300 dark:hover:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900 transition-all cursor-pointer shadow-sm hover:shadow active:scale-[0.99]"
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <IconComponent className="w-4 h-4 text-sky-500" />
                  <span className="text-xs font-semibold text-zinc-800 dark:text-zinc-200">
                    {item.title}
                  </span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400 line-clamp-2 leading-relaxed">
                {item.subtitle}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
