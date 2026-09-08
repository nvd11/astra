import React, { useState, useRef, useEffect } from 'react';
import { Cpu, ChevronDown, Check, Loader2 } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { cn } from '@/utils/cn';

const PROVIDER_COLORS: Record<string, string> = {
  Google:
    'text-amber-600 bg-amber-50 dark:bg-amber-950/50 border-amber-200 dark:border-amber-800',
  Moonshot:
    'text-purple-600 bg-purple-50 dark:bg-purple-950/50 border-purple-200 dark:border-purple-800',
  OpenAI:
    'text-sky-600 bg-sky-50 dark:bg-sky-950/50 border-sky-200 dark:border-sky-800',
  DeepSeek:
    'text-blue-600 bg-blue-50 dark:bg-blue-950/50 border-blue-200 dark:border-blue-800',
  Anthropic:
    'text-orange-600 bg-orange-50 dark:bg-orange-950/50 border-orange-200 dark:border-orange-800',
};

export const ModelSelector: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const {
    currentModel,
    setCurrentModel,
    availableModels,
    isLoadingModels,
    fetchModels,
  } = useChatStore();

  // 组件挂载时动态从 LiteLLM 网关拉取模型
  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const activeModel = availableModels.find((m) => m.id === currentModel) || {
    id: currentModel,
    name: currentModel,
    provider: 'LiteLLM',
    description: '当前在线模型',
  };

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

  const handleSelect = (modelId: string) => {
    setCurrentModel(modelId);
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
        <Cpu className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" />
        <span>{activeModel.name}</span>
        <ChevronDown
          className={cn(
            'w-3 h-3 text-zinc-400 transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {/* 悬浮 Popover 菜单 */}
      {isOpen && (
        <div className="absolute left-0 bottom-full mb-2 w-72 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between px-2.5 py-1">
            <span className="text-[10px] font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider">
              底座推理模型 (LiteLLM 动态同步)
            </span>
            {isLoadingModels && (
              <Loader2 className="w-3 h-3 text-sky-500 animate-spin" />
            )}
          </div>

          <div className="space-y-0.5 mt-1 max-h-64 overflow-y-auto">
            {availableModels.length === 0 ? (
              <div className="px-3 py-4 text-center text-xs text-zinc-400 flex items-center justify-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-500" />
                <span>正在从网关同步模型列表...</span>
              </div>
            ) : (
              availableModels.map((model) => {
                const isSelected = model.id === currentModel;
                const providerClass =
                  PROVIDER_COLORS[model.provider] ||
                  'text-zinc-600 bg-zinc-100 dark:bg-zinc-800 border-zinc-200';

                return (
                  <div
                    key={model.id}
                    onClick={() => handleSelect(model.id)}
                    className={cn(
                      'flex items-center justify-between px-2.5 py-2 rounded-xl text-xs cursor-pointer transition-all',
                      isSelected
                        ? 'bg-sky-50 dark:bg-sky-950/40 text-sky-950 dark:text-sky-200 font-medium'
                        : 'text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100/80 dark:hover:bg-zinc-800/60'
                    )}
                  >
                    <div className="truncate pr-2">
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="text-xs font-semibold truncate">
                          {model.name}
                        </span>
                        <span
                          className={cn(
                            'text-[9px] px-1.5 py-0.2 rounded border font-mono flex-shrink-0',
                            providerClass
                          )}
                        >
                          {model.provider}
                        </span>
                      </div>

                      <div className="text-[10px] text-zinc-400 dark:text-zinc-500 truncate mt-0.5 font-normal">
                        {model.description}
                      </div>
                    </div>

                    {isSelected && (
                      <Check className="w-4 h-4 text-sky-500 flex-shrink-0" />
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};
