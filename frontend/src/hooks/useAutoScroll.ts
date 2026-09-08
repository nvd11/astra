import { useState, useRef, useCallback, useEffect } from 'react';

interface UseAutoScrollOptions {
  threshold?: number; // 判定吸底的容差阈值 (默认 60px)
}

export function useAutoScroll(options?: UseAutoScrollOptions) {
  const threshold = options?.threshold ?? 60;
  const scrollRef = useRef<HTMLDivElement>(null);

  const [isAtBottom, setIsAtBottom] = useState<boolean>(true);
  const [showScrollButton, setShowScrollButton] = useState<boolean>(false);
  const isUserScrollingRef = useRef<boolean>(false);

  // 滚动到底部实现
  const scrollToBottom = useCallback((smooth = true) => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto',
    });
    setIsAtBottom(true);
    setShowScrollButton(false);
    isUserScrollingRef.current = false;
  }, []);

  // 监听容器滚动事件 (脱钩与吸底状态机)
  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;

    const currentDistanceToBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight;
    const atBottom = currentDistanceToBottom <= threshold;

    setIsAtBottom(atBottom);

    // 如果用户向上翻阅超过阈值，且容器具备可滚动高度，展示悬浮回底按钮
    if (!atBottom && el.scrollHeight > el.clientHeight + 100) {
      setShowScrollButton(true);
      isUserScrollingRef.current = true;
    } else {
      setShowScrollButton(false);
      isUserScrollingRef.current = false;
    }
  }, [threshold]);

  // 绑定滚动监听
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  // 内容变动时自动智能吸底 (仅在用户未脱钩时)
  const autoScrollIfAttached = useCallback(() => {
    if (!isUserScrollingRef.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  return {
    scrollRef,
    isAtBottom,
    showScrollButton,
    scrollToBottom,
    autoScrollIfAttached,
  };
}
