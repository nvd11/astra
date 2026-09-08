/**
 * 本地存储安全包装器 (多租户隔离与持久化会话追踪)
 */

const TOKEN_KEY = 'astra_token';
const REFRESH_TOKEN_KEY = 'astra_refresh_token';
const SESSION_ID_KEY = 'astra_device_session_id';
const THEME_KEY = 'astra_theme';

export const storage = {
  // Access Token
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },
  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  },
  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY);
  },

  // Refresh Token
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },
  setRefreshToken(token: string): void {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  },

  // 设备专属 Session ID (用于金融级全链路审计 X-Session-ID)
  getSessionId(): string {
    let sid = localStorage.getItem(SESSION_ID_KEY);
    if (!sid) {
      sid = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 'dev-session-' + Math.random().toString(36).substring(2, 15);
      localStorage.setItem(SESSION_ID_KEY, sid);
    }
    return sid;
  },

  // 主题模式 (dark / light)
  getTheme(): 'dark' | 'light' {
    const theme = localStorage.getItem(THEME_KEY);
    if (theme === 'dark') return 'dark';
    return 'light'; // 默认优雅明亮浅色
  },
  setTheme(theme: 'dark' | 'light'): void {
    localStorage.setItem(THEME_KEY, theme);
  },

  // 全量清空认证缓存
  clearAuth(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};
