import React, { useState, useEffect } from 'react';
import {
  Plus,
  MessageSquare,
  BookOpen,
  Settings,
  Sparkles,
  Trash2,
  Edit2,
  Check,
  X,
  Search,
  Loader2,
  LogOut,
  LogIn,
} from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { useAuthStore } from '@/stores/authStore';
import { Conversation } from '@/types';
import { cn } from '@/utils/cn';

interface SidebarProps {
  currentTab?: 'chat' | 'knowledge' | 'settings';
  onSelectTab?: (tab: 'chat' | 'knowledge' | 'settings') => void;
}

// 辅助函数：按时间划分会话分组 (今天 / 昨天 / 前7天 / 更早)
function groupConversations(convs: Conversation[]) {
  const today: Conversation[] = [];
  const yesterday: Conversation[] = [];
  const past7Days: Conversation[] = [];
  const older: Conversation[] = [];

  const now = new Date();
  const todayStart = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  ).getTime();
  const yesterdayStart = todayStart - 86400000;
  const past7DaysStart = todayStart - 6 * 86400000;

  for (const c of convs) {
    const time = new Date(c.updated_at || c.created_at).getTime();
    if (time >= todayStart) {
      today.push(c);
    } else if (time >= yesterdayStart) {
      yesterday.push(c);
    } else if (time >= past7DaysStart) {
      past7Days.push(c);
    } else {
      older.push(c);
    }
  }

  return [
    { title: '今天', items: today },
    { title: '昨天', items: yesterday },
    { title: '前 7 天', items: past7Days },
    { title: '更早', items: older },
  ].filter((g) => g.items.length > 0);
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab = 'chat',
  onSelectTab,
}) => {
  const {
    conversations,
    activeConversationId,
    startNewChat,
    setMobileDrawerOpen,
    fetchConversations,
    selectConversation,
    updateConversationTitle,
    deleteConversationById,
    isLoadingConversations,
  } = useChatStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const { user, fetchCurrentUser, logout, login } = useAuthStore();

  // 挂载时拉取真实用户信息与会话列表
  useEffect(() => {
    fetchCurrentUser();
    fetchConversations();
  }, [fetchCurrentUser, fetchConversations]);

  const handleSelectConversation = (id: string) => {
    selectConversation(id);
    setMobileDrawerOpen(false);
    if (onSelectTab) onSelectTab('chat');
  };

  const handleNewChat = () => {
    startNewChat();
    setMobileDrawerOpen(false);
    if (onSelectTab) onSelectTab('chat');
  };

  const handleStartRename = (conv: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const handleSaveRename = (id: string, e: React.MouseEvent | React.FormEvent) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      updateConversationTitle(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(null);
  };

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    deleteConversationById(id);
  };

  // 根据搜索关键字过滤
  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const grouped = groupConversations(filteredConversations);

  return (
    <aside className="h-full w-64 flex flex-col bg-zinc-50 dark:bg-zinc-950 border-r border-zinc-200/80 dark:border-zinc-800 select-none">
      {/* 顶部 Logo 与新对话按钮 */}
      <div className="p-3.5 space-y-3">
        <div className="flex items-center gap-2.5 px-2 py-1">
          <div className="w-7 h-7 rounded-lg bg-sky-500 flex items-center justify-center text-white shadow-sm shadow-sky-500/20">
            <Sparkles className="w-4 h-4 fill-current" />
          </div>
          <span className="font-bold text-base tracking-tight text-zinc-900 dark:text-white">
            Astra
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-200/80 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 font-mono">
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

        {/* 快速搜索框 */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索历史会话..."
            className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/80 text-zinc-800 dark:text-zinc-200 placeholder:text-zinc-400 focus:outline-none focus:border-sky-500"
          />
          <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      {/* 模块化功能中枢导航 */}
      <div className="px-3 py-1 space-y-1">
        <button
          onClick={() => onSelectTab && onSelectTab('chat')}
          className={cn(
            'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
            currentTab === 'chat'
              ? 'bg-zinc-200/80 dark:bg-zinc-800 text-zinc-900 dark:text-white font-semibold'
              : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/50 dark:hover:bg-zinc-900'
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
              ? 'bg-zinc-200/80 dark:bg-zinc-800 text-zinc-900 dark:text-white font-semibold'
              : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/50 dark:hover:bg-zinc-900'
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

      {/* 真实会话历史列表 (带时间分组与就地重命名) */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
        {isLoadingConversations && conversations.length === 0 ? (
          <div className="flex items-center justify-center gap-2 py-6 text-xs text-zinc-400">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-500" />
            <span>加载会话中...</span>
          </div>
        ) : grouped.length === 0 ? (
          <div className="py-8 text-center text-xs text-zinc-400">
            {searchQuery ? '未找到相关会话' : '暂无历史对话'}
          </div>
        ) : (
          grouped.map((group) => (
            <div key={group.title} className="space-y-0.5">
              <div className="px-2 py-1 text-[10px] font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider">
                {group.title}
              </div>

              {group.items.map((conv) => {
                const isActive = conv.id === activeConversationId;
                const isEditing = conv.id === editingId;

                return (
                  <div
                    key={conv.id}
                    onClick={() => !isEditing && handleSelectConversation(conv.id)}
                    className={cn(
                      'group relative flex items-center justify-between px-2.5 py-2 rounded-lg text-xs cursor-pointer transition-all',
                      isActive
                        ? 'bg-white dark:bg-zinc-800/90 text-zinc-900 dark:text-white font-medium shadow-xs border border-zinc-200/80 dark:border-transparent'
                        : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/50 dark:hover:bg-zinc-900/60'
                    )}
                  >
                    {isEditing ? (
                      <div
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-1 w-full"
                      >
                        <input
                          type="text"
                          autoFocus
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveRename(conv.id, e);
                            if (e.key === 'Escape') setEditingId(null);
                          }}
                          className="flex-1 px-1.5 py-0.5 text-xs bg-white dark:bg-zinc-900 border border-sky-500 rounded text-zinc-900 dark:text-white focus:outline-none"
                        />
                        <button
                          type="button"
                          onClick={(e) => handleSaveRename(conv.id, e)}
                          className="p-1 text-emerald-600 hover:bg-emerald-50 rounded"
                        >
                          <Check className="w-3 h-3" />
                        </button>
                        <button
                          type="button"
                          onClick={handleCancelRename}
                          className="p-1 text-zinc-400 hover:bg-zinc-100 rounded"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center gap-2 truncate pr-10">
                          <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
                          <span className="truncate">{conv.title}</span>
                        </div>

                        {/* 悬浮快捷重命名与删除 */}
                        <div className="absolute right-1.5 opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition-opacity">
                          <button
                            type="button"
                            onClick={(e) => handleStartRename(conv, e)}
                            className="p-1 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 rounded hover:bg-zinc-200/60 dark:hover:bg-zinc-700"
                            title="重命名"
                          >
                            <Edit2 className="w-3 h-3" />
                          </button>
                          <button
                            type="button"
                            onClick={(e) => handleDelete(conv.id, e)}
                            className="p-1 text-zinc-400 hover:text-red-500 rounded hover:bg-red-50 dark:hover:bg-red-950/40"
                            title="删除会话"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          ))
        )}
      </div>

      {/* 底部设置与用户身份区 */}
      <div className="p-3 border-t border-zinc-200 dark:border-zinc-800/80 flex flex-col gap-2">
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

        {user && user.id !== 'anonymous' ? (
          <div className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-zinc-100/90 dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800">
            <div className="flex items-center gap-2 truncate min-w-0">
              {user.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.username}
                  className="w-7 h-7 rounded-full object-cover border border-zinc-300 dark:border-zinc-700 flex-shrink-0"
                />
              ) : (
                <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-sky-500 to-indigo-500 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
                  {user.username.slice(0, 1).toUpperCase()}
                </div>
              )}
              <div className="flex flex-col truncate">
                <span className="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate leading-tight">
                  {user.username}
                </span>
                <span className="text-[10px] text-zinc-500 dark:text-zinc-400 truncate leading-tight mt-0.5">
                  {user.email || 'GitHub 认证'}
                </span>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-1.5 text-zinc-400 hover:text-red-500 dark:hover:text-red-400 rounded-md hover:bg-zinc-200/60 dark:hover:bg-zinc-800 transition-colors flex-shrink-0 ml-1"
              title="退出登录 (注销全站 Cookie)"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={login}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 transition-colors shadow-sm"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>使用 GitHub 登录</span>
          </button>
        )}
      </div>
    </aside>
  );
};
