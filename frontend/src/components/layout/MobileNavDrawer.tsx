import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { Sidebar } from './Sidebar';

interface MobileNavDrawerProps {
  currentTab?: 'chat' | 'knowledge' | 'settings';
  onSelectTab?: (tab: 'chat' | 'knowledge' | 'settings') => void;
}

export const MobileNavDrawer: React.FC<MobileNavDrawerProps> = ({
  currentTab,
  onSelectTab,
}) => {
  const { isMobileDrawerOpen, setMobileDrawerOpen } = useChatStore();

  // 监听 ESC 键关闭抽屉
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setMobileDrawerOpen(false);
      }
    };
    if (isMobileDrawerOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMobileDrawerOpen, setMobileDrawerOpen]);

  if (!isMobileDrawerOpen) return null;

  return (
    <div className="lg:hidden fixed inset-0 z-50 flex">
      {/* 半透明毛玻璃遮罩 */}
      <div
        onClick={() => setMobileDrawerOpen(false)}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity animate-in fade-in"
      />

      {/* 侧滑抽屉面板 */}
      <div className="relative w-72 max-w-[80vw] h-full z-10 shadow-2xl animate-in slide-in-from-left duration-300">
        <button
          onClick={() => setMobileDrawerOpen(false)}
          className="absolute top-3.5 right-3 p-1.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 rounded-lg z-20"
          title="关闭菜单"
        >
          <X className="w-5 h-5" />
        </button>
        <Sidebar currentTab={currentTab} onSelectTab={onSelectTab} />
      </div>
    </div>
  );
};
