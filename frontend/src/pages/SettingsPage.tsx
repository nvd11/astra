import React, { useState } from 'react';
import {
  Settings,
  Laptop,
  Smartphone,
  CheckCircle2,
  Trash2,
  Activity,
} from 'lucide-react';
import { UserSessionItem, UsageStats } from '@/types';

export const SettingsPage: React.FC = () => {
  // 模拟当前用户的多设备活跃会话
  const [sessions, setSessions] = useState<UserSessionItem[]>([
    {
      id: 'sess-1',
      device_info: 'MacBook Pro (M3 Max / macOS 15.1)',
      ip_address: '10.0.1.3',
      last_active_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 86400000 * 7).toISOString(),
      is_current: true, // 当前设备绿标
    },
    {
      id: 'sess-2',
      device_info: 'iPhone 16 Pro (iOS 18.2 / Safari)',
      ip_address: '113.108.72.19',
      last_active_at: new Date(Date.now() - 7200000).toISOString(),
      expires_at: new Date(Date.now() + 86400000 * 6).toISOString(),
      is_current: false,
    },
  ]);

  // 模拟用量统计
  const [stats] = useState<UsageStats>({
    total_messages: 142,
    total_tokens: 38520,
    total_conversations: 28,
    today_messages: 18,
    today_tokens: 4210,
  });

  const handleRevokeSession = (sessionId: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
  };

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-50 dark:bg-zinc-950 p-6 sm:p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* 页面标题 */}
        <div className="border-b border-zinc-200 dark:border-zinc-800 pb-4">
          <h1 className="text-xl font-bold text-zinc-900 dark:text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-sky-500" />
            系统与安全设置
          </h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
            管理金融级全链路审计多设备会话，查看实时 Token 消耗与账号偏好。
          </p>
        </div>

        {/* 用量统计仪表盘 */}
        <div className="space-y-3">
          <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-sky-500" />
            <span>实时用量概览</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
              <span className="text-[11px] text-zinc-500">累计会话数</span>
              <div className="text-xl font-bold text-zinc-900 dark:text-white mt-1">
                {stats.total_conversations}
              </div>
            </div>

            <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
              <span className="text-[11px] text-zinc-500">累计消息数</span>
              <div className="text-xl font-bold text-zinc-900 dark:text-white mt-1">
                {stats.total_messages}
              </div>
            </div>

            <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
              <span className="text-[11px] text-zinc-500">今日消耗 Token</span>
              <div className="text-xl font-bold text-sky-600 dark:text-sky-400 mt-1">
                {stats.today_tokens.toLocaleString()}
              </div>
            </div>

            <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
              <span className="text-[11px] text-zinc-500">总消耗 Token</span>
              <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
                {stats.total_tokens.toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        {/* 多设备活跃会话管理 (金融级审计溯源) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              活跃设备会话 ({sessions.length})
            </div>
            <span className="text-[11px] text-zinc-400">
              自动关联后端 user_sessions 表，支持单键撤销其他设备登录态
            </span>
          </div>

          <div className="space-y-2.5">
            {sessions.map((sess) => {
              const isMobile = sess.device_info.toLowerCase().includes('iphone') || sess.device_info.toLowerCase().includes('android');
              return (
                <div
                  key={sess.id}
                  className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-zinc-600 dark:text-zinc-400 flex-shrink-0">
                      {isMobile ? (
                        <Smartphone className="w-5 h-5" />
                      ) : (
                        <Laptop className="w-5 h-5" />
                      )}
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-zinc-800 dark:text-zinc-200">
                          {sess.device_info}
                        </span>
                        {sess.is_current && (
                          <span className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-0.5 rounded-full border border-emerald-500/20 font-medium">
                            <CheckCircle2 className="w-3 h-3" />
                            当前设备
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-zinc-400 mt-0.5">
                        IP: {sess.ip_address} · 会话 ID: {sess.id.slice(0, 8)}...
                      </div>
                    </div>
                  </div>

                  {!sess.is_current && (
                    <button
                      onClick={() => handleRevokeSession(sess.id)}
                      className="px-3 py-1.5 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-lg transition-colors flex items-center gap-1"
                      title="强制下线该设备"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>下线</span>
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
