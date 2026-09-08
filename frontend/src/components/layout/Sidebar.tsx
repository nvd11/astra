import React from 'react';
import {
  Plus,
  MessageSquare,
  BookOpen,
  Settings,
  Sparkles,
  Trash2,
  Share2,
} from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { cn } from '@/utils/cn';

interface SidebarProps {
  currentTab?: 'chat' | 'knowledge' | 'settings';
  onSelectTab?: (tab: 'chat' | 'knowledge' | 'settings') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab = 'chat',
  onSelectTab,
}) => {
  const {
    conversations,
    activeConversationId,
    setActiveConversationId,
    startNewChat,
    setMobileDrawerOpen,
  } = useChatStore();

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id);
    setMobileDrawerOpen(false);
    if (onSelectTab) onSelectTab('chat');
  };

  const handleNewChat = () => {
    startNewChat();
    setMobileDrawerOpen(false);
    if (onSelectTab) onSelectTab('chat');
  };

  return (
    <aside className="h-full w-64 flex flex-col bg-zinc-100/70 dark:bg-zinc-950 border-r border-zinc-200 dark:border-zinc-800 select-none">
      {/* 顶部 Logo 与新对话按钮 */}
      <div className="p-3.5 space-y-3">
        <div className="flex items-center gap-2.5 px-2 py-1">
          <div className="w-7 h-7 rounded-lg bg-sky-500 flex items-center justify-center text-white shadow-sm shadow-sky-500/20">
            <Sparkles className="w-4 h-4 fill-current" />
          </div>
          <span className="font-bold text-base tracking-tight text-zinc-900 dark:text-white">
            Astra
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-200 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 font-mono">
            v1.0
          </span>
        </div>

        {/* "+ 新对话" 按钮 */}
        <button
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 transition-all font-medium text-sm shadow-sm active:scale-[0.98]"
        >
          <Plus className="w-4 h-4" />
          <span>新对话</span>
        </button>
      </div>

      {/* 模块化功能中枢导航 */}
      <div className="px-3 py-1 space-y-1">
        <button
          onClick={() => onSelectTab && onSelectTab('chat')}
          className={cn(
            'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
            currentTab === 'chat'
              ? 'bg-zinc-200/80 dark:bg-zinc-800 text-zinc-900 dark:text-white'
              : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/40 dark:hover:bg-zinc-900'
          )}
        >
          <MessageSquare className="w-4 h-4" />
          <span>对话工作台</span>
        </button>

        <button
          onClick={() => onSelectTab && onSelectTab('knowledge')}
          className={cn(
            'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
            currentTab === 'knowledge'
              ? 'bg-zinc-200/80 dark:bg-zinc-800 text-zinc-900 dark:text-white'
              : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/40 dark:hover:bg-zinc-900'
          )}
        >
          <BookOpen className="w-4 h-4 text-emerald-500" />
          <div className="flex-1 text-left flex items-center justify-between">
            <span>RAG 知识库</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-500 font-normal">
              HeatWave
            </span>
          </div>
        </button>
      </div>

      {/* 历史会话列表 */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        <div className="px-3 py-1.5 text-[11px] font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider">
          近期会话
        </div>

        {conversations.map((conv) => {
          const isActive = conv.id === activeConversationId;
          return (
            <div
              key={conv.id}
              onClick={() => handleSelectConversation(conv.id)}
              className={cn(
                'group relative flex items-center justify-between px-3 py-2.5 rounded-lg text-xs cursor-pointer transition-all',
                isActive
                  ? 'bg-zinc-200/80 dark:bg-zinc-800/90 text-zinc-900 dark:text-white font-medium'
                  : 'text-zinc-700 dark:text-zinc-400 hover:bg-zinc-200/40 dark:hover:bg-zinc-900/60'
              )}
            >
              <div className="flex items-center gap-2 truncate pr-6">
                <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
                <span className="truncate">{conv.title}</span>
              </div>

              {/* 悬停快捷菜单 */}
              <div className="absolute right-2 opacity-0 group-hover:opacity-100 flex items-center gap-1 transition-opacity">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                  }}
                  className="p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 rounded"
                  title="分享"
                >
                  <Share2 className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                  }}
                  className="p-1 text-zinc-400 hover:text-red-500 rounded"
                  title="删除"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* 底部设置入口 */}
      <div className="p-3 border-t border-zinc-200 dark:border-zinc-800/80">
        <button
          onClick={() => onSelectTab && onSelectTab('settings')}
          className={cn(
            'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
            currentTab === 'settings'
              ? 'bg-zinc-200/80 dark:bg-zinc-800 text-zinc-900 dark:text-white'
              : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/40 dark:hover:bg-zinc-900'
          )}
        >
          <Settings className="w-4 h-4" />
          <span>设置与设备管理</span>
        </button>
      </div>
    </aside>
  );
};
