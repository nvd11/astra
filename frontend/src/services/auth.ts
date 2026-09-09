import { BaseResponse, User } from '@/types';
import { api } from './api';

export const authService = {
  /**
   * 获取当前登录用户信息 (来自 Kong Forward-Auth 注入或 JWT)
   */
  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await api.get<BaseResponse<User>>('/auth/me');
      if (response.data && response.data.code === 0) {
        return response.data.data;
      }
      return null;
    } catch (err) {
      console.warn('Failed to get current user from /auth/me:', err);
      return null;
    }
  },

  /**
   * 触发 Kong 网关级登出 (重定向至 OAuth2-Proxy 清除 .jppwl.asia 根域 Cookie)
   */
  gatewayLogout(): void {
    window.location.href = '/oauth2/sign_out?rd=/astra/';
  },

  /**
   * 触发 Kong 网关登录重定向 (携带当前页面路径用于回跳)
   */
  gatewayLogin(): void {
    const returnPath = window.location.pathname.startsWith('/astra')
      ? window.location.pathname
      : '/astra/';
    window.location.href = `/oauth2/start?rd=${encodeURIComponent(returnPath)}`;
  },
};
