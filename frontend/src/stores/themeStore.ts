import { create } from 'zustand';
import { storage } from '@/utils/storage';

interface ThemeState {
  theme: 'dark' | 'light';
  toggleTheme: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
}

export const useThemeStore = create<ThemeState>((set) => {
  const initialTheme = storage.getTheme();

  // 初始化设置 html class
  if (typeof document !== 'undefined') {
    if (initialTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  return {
    theme: initialTheme,
    toggleTheme: () =>
      set((state) => {
        const nextTheme = state.theme === 'dark' ? 'light' : 'dark';
        storage.setTheme(nextTheme);

        if (nextTheme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }

        return { theme: nextTheme };
      }),
    setTheme: (theme) => {
      storage.setTheme(theme);
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      set({ theme });
    },
  };
});
