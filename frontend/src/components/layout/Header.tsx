import React from 'react';
import { Menu, PanelLeftClose, PanelLeft, Moon, Sun, Sparkles } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { useThemeStore } from '@/stores/themeStore';
import { AVAILABLE_MODELS } from '@/types';

export const Header: React.FC = () => {
  const {
    isSidebarOpen,
    toggleSidebar,
    toggleMobileDrawer,
    currentModel,
  } = useChatStore();
  const { theme, toggleTheme } = useThemeStore();

  const modelInfo = AVAILABLE_MODELS.find((m) => m.id === currentModel) || AVAILABLE_MODELS[0];

  return (
    <header className="h-14 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md px-4 flex items-center justify-between z-10 select-none">
      {/* 左侧控制区 */}
      <div className="flex items-center gap-3">
        {/* 移动端汉堡菜单按钮 */}
        <button
          onClick={toggleMobileDrawer}
          className="lg:hidden p-2 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-900 rounded-lg transition-colors"
          title="打开侧边菜单"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* 桌面端折叠/展开侧边栏按钮 */}
        <button
          onClick={toggleSidebar}
          className="hidden lg:flex p-2 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-900 rounded-lg transition-colors"
          title={isSidebarOpen ? '折叠侧边栏 (Ctrl+B)' : '展开侧边栏 (Ctrl+B)'}
        >
          {isSidebarOpen ? (
            <PanelLeftClose className="w-5 h-5" />
          ) : (
            <PanelLeft className="w-5 h-5" />
          )}
        </button>

        {/* 当前模型标识徽章 */}
        <div className="flex items-center gap-2 px-2.5 py-1 bg-zinc-100 dark:bg-zinc-900 rounded-full border border-zinc-200 dark:border-zinc-800">
          <Sparkles className="w-3.5 h-3.5 text-sky-500" />
          <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
            {modelInfo.name}
          </span>
        </div>
      </div>

      {/* 右侧动作区 */}
      <div className="flex items-center gap-2">
        {/* 深浅色模式切换 */}
        <button
          onClick={toggleTheme}
          className="p-2 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-900 rounded-lg transition-colors"
          title={theme === 'dark' ? '切换为浅色模式' : '切换为暗黑模式'}
        >
          {theme === 'dark' ? (
            <Sun className="w-5 h-5 text-amber-400" />
          ) : (
            <Moon className="w-5 h-5 text-zinc-600" />
          )}
        </button>

        {/* 用户头像占位 */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-sky-500 to-indigo-500 flex items-center justify-center text-white text-xs font-semibold shadow-sm">
          A
        </div>
      </div>
    </header>
  );
};
