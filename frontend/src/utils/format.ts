/**
 * 友好时间转换 (刚刚 / N分钟前 / 昨天 / 日期)
 */
export function formatTimeAgo(dateInput: string | Date): string {
  const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return '刚刚';
  }
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} 分钟前`;
  }
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} 小时前`;
  }
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays === 1) {
    return '昨天';
  }
  if (diffInDays < 7) {
    return `${diffInDays} 天前`;
  }

  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
  });
}

/**
 * 格式化 Token 计数 (如 1,234 或 12.5k)
 */
export function formatTokens(num: number): string {
  if (num >= 1_000_000) {
    return (num / 1_000_000).toFixed(1) + 'M';
  }
  if (num >= 1_000) {
    return (num / 1_000).toFixed(1) + 'k';
  }
  return num.toLocaleString();
}

/**
 * 截断文本
 */
export function truncateText(str: string, maxLength = 24): string {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + '...';
}
