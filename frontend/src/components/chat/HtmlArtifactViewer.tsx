import React, { useState } from 'react';
import {
  Play,
  Code2,
  RotateCw,
  Copy,
  Check,
  Maximize2,
  Minimize2,
  Download,
  Loader2,
} from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { cn } from '@/utils/cn';

interface HtmlArtifactViewerProps {
  code: string;
  title?: string;
}

export const HtmlArtifactViewer: React.FC<HtmlArtifactViewerProps> = ({
  code,
  title = '动态交互微应用',
}) => {
  const [activeTab, setActiveTab] = useState<'preview' | 'code'>('preview');
  const [copied, setCopied] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [reloadKey, setReloadKey] = useState<number>(0);
  const { isStreaming } = useChatStore();

  // 组装注入 Tailwind 运行时与安全重置的沙箱文档
  const generateSrcDoc = (rawCode: string): string => `
    <!DOCTYPE html>
    <html lang="zh-CN">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif;
            margin: 0;
            padding: 16px;
            box-sizing: border-box;
            background-color: transparent;
          }
          * { box-sizing: border-box; }
        </style>
      </head>
      <body>
        ${rawCode}
      </body>
    </html>
  `;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.warn('Copy failed:', e);
    }
  };

  const handleDownload = () => {
    const fullHtml = generateSrcDoc(code);
    const blob = new Blob([fullHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `astra-artifact-${Date.now()}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className={cn(
        'my-3.5 rounded-2xl border border-zinc-200/90 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm overflow-hidden transition-all',
        isFullscreen &&
          'fixed inset-4 sm:inset-8 z-50 shadow-2xl flex flex-col my-0 border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900'
      )}
    >
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between px-3.5 py-2 border-b border-zinc-100 dark:border-zinc-800/70 bg-zinc-50/80 dark:bg-zinc-950/80 select-none">
        <div className="flex items-center gap-2.5">
          {/* 双态选项卡切换 */}
          <div className="flex items-center bg-zinc-200/70 dark:bg-zinc-800 p-0.5 rounded-lg text-xs font-medium">
            <button
              type="button"
              onClick={() => setActiveTab('preview')}
              className={cn(
                'flex items-center gap-1.5 px-2.5 py-1 rounded-md transition-all',
                activeTab === 'preview'
                  ? 'bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white shadow-xs font-semibold'
                  : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white'
              )}
            >
              <Play className="w-3 h-3 text-emerald-500 fill-current" />
              <span>实时预览</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('code')}
              className={cn(
                'flex items-center gap-1.5 px-2.5 py-1 rounded-md transition-all',
                activeTab === 'code'
                  ? 'bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white shadow-xs font-semibold'
                  : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white'
              )}
            >
              <Code2 className="w-3 h-3 text-sky-500" />
              <span>源码</span>
            </button>
          </div>

          <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 hidden sm:inline truncate max-w-[200px]">
            {title}
          </span>
        </div>

        {/* 右侧实用工具集 */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setReloadKey((k) => k + 1)}
            className="p-1.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            title="重新加载沙箱状态"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={handleCopy}
            className="p-1.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            title="复制代码"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-emerald-500" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
          <button
            type="button"
            onClick={handleDownload}
            className="p-1.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            title="导出为独立 HTML 文件"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            title={isFullscreen ? '退出全屏' : '全屏聚焦'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-3.5 h-3.5" />
            ) : (
              <Maximize2 className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      </div>

      {/* 主体展示区 */}
      <div className={cn('relative w-full bg-zinc-50 dark:bg-zinc-950', isFullscreen ? 'flex-1' : 'h-80 sm:h-96')}>
        {activeTab === 'preview' ? (
          isStreaming ? (
            <div className="w-full h-full flex flex-col items-center justify-center gap-3 bg-zinc-50/80 dark:bg-zinc-950/80 text-zinc-500 select-none p-6 text-center">
              <Loader2 className="w-7 h-7 text-sky-500 animate-spin" />
              <div className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                微应用代码正在实时生成中...
              </div>
              <p className="text-[11px] text-zinc-400 max-w-sm leading-relaxed">
                为保证流畅性能，生成完毕后将自动装载执行；点击上方“源码”选项卡可实时查看代码编写进度。
              </p>
            </div>
          ) : (
            <iframe
              key={reloadKey}
              srcDoc={generateSrcDoc(code)}
              sandbox="allow-scripts allow-modals"
              className="w-full h-full border-0 bg-white"
              title={title}
            />
          )
        ) : (
          <pre className="w-full h-full p-4 m-0 overflow-auto bg-zinc-950 text-zinc-200 font-mono text-xs leading-relaxed selection:bg-sky-500/30">
            <code>{code}</code>
          </pre>
        )}
      </div>
    </div>
  );
};
