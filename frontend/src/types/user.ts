/**
 * 当前登录用户实体 (与后端 UserInfoData 严格一致)
 */
export interface User {
  id: string;
  username: string;
  email: string | null;
  avatar_url: string | null;
  preferences: Record<string, unknown>;
  default_model: string;
  default_agent: string;
  created_at: string;
}

/**
 * 活跃设备会话实体 (与后端 UserSessionItem 严格一致)
 */
export interface UserSessionItem {
  id: string;
  device_info: string;
  ip_address: string;
  last_active_at: string;
  expires_at: string;
  is_current: boolean;
}

/**
 * 用户用量聚合统计 (与后端 UsageStatsData 严格一致)
 */
export interface UsageStats {
  total_messages: number;
  total_tokens: number;
  total_conversations: number;
  today_messages: number;
  today_tokens: number;
}
