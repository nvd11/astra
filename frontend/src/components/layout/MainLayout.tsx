import React, { useEffect } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MobileNavDrawer } from './MobileNavDrawer';
import { useChatStore } from '@/stores/chatStore';
import { useResponsive } from '@/hooks/useMediaQuery';

interface MainLayoutProps {
  currentTab: 'chat' | 'knowledge' | 'settings';
  onSelectTab: (tab: 'chat' | 'knowledge' | 'settings') => void;
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  currentTab,
  onSelectTab,
  children,
}) => {
  const { isSidebarOpen, toggleSidebar } = useChatStore();
  const { isDesktop } = useResponsive();

  // 监听键盘快捷键 Ctrl/Cmd + B 切换侧边栏
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        toggleSidebar();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleSidebar]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white dark:bg-zinc-950 font-sans text-zinc-900 dark:text-zinc-100">
      {/* 桌面端常驻侧边栏 (支持平滑宽度折叠) */}
      {isDesktop && isSidebarOpen && (
        <div className="h-full flex-shrink-0 animate-in slide-in-from-left duration-200">
          <Sidebar currentTab={currentTab} onSelectTab={onSelectTab} />
        </div>
      )}

      {/* 移动端侧滑抽屉浮层 */}
      <MobileNavDrawer currentTab={currentTab} onSelectTab={onSelectTab} />

      {/* 右侧核心工作区 (Header + 内容视图) */}
      <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative">
        <Header />
        <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
};
