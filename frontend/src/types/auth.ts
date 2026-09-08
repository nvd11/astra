import { User } from './user';

/**
 * 认证令牌载荷 (与后端 TokenResponseData 严格一致)
 */
export interface TokenData {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

/**
 * 认证状态
 */
export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
