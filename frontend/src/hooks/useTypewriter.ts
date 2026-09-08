import { useState, useRef, useCallback, useEffect } from 'react';

interface UseTypewriterOptions {
  onComplete?: (fullText: string) => void;
}

export function useTypewriter(options?: UseTypewriterOptions) {
  const [displayedText, setDisplayedText] = useState<string>('');
  const [isTyping, setIsTyping] = useState<boolean>(false);

  // 先进先出 (FIFO) 字符缓冲池
  const queueRef = useRef<string[]>([]);
  const rafIdRef = useRef<number | null>(null);
  const streamEndedRef = useRef<boolean>(false);
  const currentTextRef = useRef<string>('');

  // 同步 ref 避免闭包旧值
  currentTextRef.current = displayedText;

  const runLoop = useCallback(() => {
    const loop = () => {
      if (queueRef.current.length === 0) {
        if (streamEndedRef.current) {
          setIsTyping(false);
          rafIdRef.current = null;
          if (options?.onComplete) {
            options.onComplete(currentTextRef.current);
          }
          return;
        }
        // 缓冲池暂时消费完毕，继续等待新 chunk 注入
        rafIdRef.current = requestAnimationFrame(loop);
        return;
      }

      // 动态自适应步长算法 (Dynamic Catch-up Step)
      // 队列积压大时加速消费，队列平缓时从容优雅
      const backlog = queueRef.current.length;
      let stepCount = 1;
      if (backlog > 100) {
        stepCount = 8;
      } else if (backlog > 50) {
        stepCount = 4;
      } else if (backlog > 20) {
        stepCount = 2;
      }

      const consumedChars = queueRef.current.splice(0, stepCount).join('');
      setDisplayedText((prev) => prev + consumedChars);

      rafIdRef.current = requestAnimationFrame(loop);
    };

    if (rafIdRef.current === null) {
      rafIdRef.current = requestAnimationFrame(loop);
    }
  }, [options]);

  /**
   * 向缓冲池注入新的文本增量
   */
  const enqueue = useCallback(
    (chunk: string) => {
      if (!chunk) return;
      setIsTyping(true);
      // 将 chunk 切割为单字符进入待消费队列
      for (const char of chunk) {
        queueRef.current.push(char);
      }
      runLoop();
    },
    [runLoop]
  );

  /**
   * 标记数据流结束
   */
  const endStream = useCallback(() => {
    streamEndedRef.current = true;
    runLoop();
  }, [runLoop]);

  /**
   * 瞬间冲刷消费所有剩余缓冲 (用于点击立即停止时)
   */
  const flush = useCallback(() => {
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    const remaining = queueRef.current.join('');
    queueRef.current = [];
    streamEndedRef.current = true;
    setIsTyping(false);

    if (remaining) {
      setDisplayedText((prev) => {
        const full = prev + remaining;
        if (options?.onComplete) options.onComplete(full);
        return full;
      });
    } else if (options?.onComplete) {
      options.onComplete(currentTextRef.current);
    }
  }, [options]);

  /**
   * 完全重置打字机状态
   */
  const reset = useCallback(() => {
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    queueRef.current = [];
    streamEndedRef.current = false;
    setIsTyping(false);
    setDisplayedText('');
  }, []);

  // 组件卸载时安全清理 RAF 句柄
  useEffect(() => {
    return () => {
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);

  return {
    displayedText,
    isTyping,
    enqueue,
    endStream,
    flush,
    reset,
  };
}
