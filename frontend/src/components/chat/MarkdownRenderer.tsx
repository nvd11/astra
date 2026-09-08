import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Check, Copy } from 'lucide-react';
import { HtmlArtifactViewer } from './HtmlArtifactViewer';
import { cn } from '@/utils/cn';
import 'katex/dist/katex.min.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className,
}) => {
  return (
    <div className={cn('text-sm leading-relaxed break-words space-y-2.5', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code({ inline, className: codeClassName, children, ...props }: { inline?: boolean; className?: string; children?: React.ReactNode }) {
            const match = /language-(\w+)/.exec(codeClassName || '');
            const lang = match ? match[1].toLowerCase() : '';
            const codeString = String(children).replace(/\n$/, '');

            // 1. 如果是 HTML 且包含可执行 DOM 标签，自动升格为 Claude 式零信任交互沙箱
            if (
              !inline &&
              lang === 'html' &&
              (codeString.includes('<div') ||
                codeString.includes('<html') ||
                codeString.includes('<canvas') ||
                codeString.includes('<script') ||
                codeString.includes('<button') ||
                codeString.includes('<svg'))
            ) {
              return (
                <HtmlArtifactViewer
                  code={codeString}
                  title="动态 HTML 交互沙箱组件"
                />
              );
            }

            // 2. 常规多行代码块：带高亮与一键复制代码按钮
            if (!inline && match) {
              return <CodeBlock language={lang} code={codeString} />;
            }

            // 3. 行内小代码标签
            return (
              <code
                className={cn(
                  'px-1.5 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-sky-600 dark:text-sky-400 font-mono text-xs border border-zinc-200/50 dark:border-zinc-700/50',
                  codeClassName
                )}
                {...props}
              >
                {children}
              </code>
            );
          },

          // 响应式表格组件
          table({ children }) {
            return (
              <div className="overflow-x-auto my-3 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-xs">
                <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800 text-xs">
                  {children}
                </table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="px-3.5 py-2.5 bg-zinc-50 dark:bg-zinc-900 font-semibold text-left text-zinc-800 dark:text-zinc-200 border-b border-zinc-200 dark:border-zinc-800">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="px-3.5 py-2 border-t border-zinc-100 dark:border-zinc-800/60 text-zinc-700 dark:text-zinc-300">
                {children}
              </td>
            );
          },

          // 引用块
          blockquote({ children }) {
            return (
              <blockquote className="border-l-3 border-sky-500 pl-3.5 py-1 my-2 text-zinc-600 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-900/40 rounded-r-lg italic text-xs">
                {children}
              </blockquote>
            );
          },

          // 超链接外链安全标记
          a({ href, children }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sky-600 dark:text-sky-400 hover:underline font-medium"
              >
                {children}
              </a>
            );
          },

          // 标题增强
          h1({ children }) {
            return (
              <h1 className="text-lg font-bold text-zinc-900 dark:text-white mt-4 mb-2 pb-1 border-b border-zinc-100 dark:border-zinc-800">
                {children}
              </h1>
            );
          },
          h2({ children }) {
            return (
              <h2 className="text-base font-bold text-zinc-900 dark:text-white mt-3 mb-1.5">
                {children}
              </h2>
            );
          },
          h3({ children }) {
            return (
              <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mt-2.5 mb-1">
                {children}
              </h3>
            );
          },

          // 列表
          ul({ children }) {
            return <ul className="list-disc list-outside pl-4 space-y-1 my-1.5">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal list-outside pl-4 space-y-1 my-1.5">{children}</ol>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.warn('Copy failed:', e);
    }
  };

  return (
    <div className="relative my-3 rounded-xl overflow-hidden border border-zinc-200 dark:border-zinc-800 bg-zinc-950 font-mono text-xs shadow-sm">
      {/* 顶部语言与复制栏 */}
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-zinc-900/90 border-b border-zinc-800/80 text-zinc-400 select-none">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-300">
          {language || 'code'}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-[11px] text-zinc-400 hover:text-white transition-colors"
          title="复制代码"
        >
          {copied ? (
            <Check className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <Copy className="w-3.5 h-3.5" />
          )}
          <span>{copied ? '已复制' : '复制'}</span>
        </button>
      </div>

      <SyntaxHighlighter
        style={vscDarkPlus}
        language={language}
        PreTag="div"
        customStyle={{
          margin: 0,
          padding: '12px 14px',
          background: 'transparent',
          fontSize: '12px',
          lineHeight: '1.6',
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
