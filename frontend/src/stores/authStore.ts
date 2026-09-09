import { create } from 'zustand';
import { User } from '@/types';
import { authService } from '@/services/auth';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  fetchCurrentUser: () => Promise<User | null>;
  logout: () => void;
  login: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  isAuthenticated: false,
  error: null,

  fetchCurrentUser: async () => {
    set({ isLoading: true, error: null });
    try {
      const user = await authService.getCurrentUser();
      set({
        user,
        isAuthenticated: !!user && user.id !== 'anonymous',
        isLoading: false,
      });
      return user;
    } catch (err) {
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to authenticate',
      });
      return null;
    }
  },

  logout: () => {
    set({ user: null, isAuthenticated: false });
    authService.gatewayLogout();
  },

  login: () => {
    authService.gatewayLogin();
  },
}));
