import React, { useState } from 'react';
import { BookOpen, UploadCloud, Search, Database, Layers, CheckCircle2 } from 'lucide-react';
import { KnowledgeDocument } from '@/types';

export const KnowledgePage: React.FC = () => {
  const [docs] = useState<KnowledgeDocument[]>([
    {
      id: 'doc-1',
      title: 'HSBC_Global_Private_Banking_Architecture_2026.pdf',
      file_type: 'pdf',
      chunk_count: 48,
      status: 'indexed',
      created_at: '2026-09-07T10:00:00Z',
    },
    {
      id: 'doc-2',
      title: 'MySQL_HeatWave_Vector_Search_Engine_Spec.md',
      file_type: 'md',
      chunk_count: 16,
      status: 'indexed',
      created_at: '2026-09-06T14:30:00Z',
    },
  ]);

  const [query, setQuery] = useState('');
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleTestSearch = () => {
    if (!query.trim()) return;
    setTestResult(
      `基于 OCI MySQL HeatWave 原生 VECTOR(1536) 相似度检索命中 Top-1 切片：\n\n【来源文档: MySQL_HeatWave_Vector_Search_Engine_Spec.md / Chunk #3 (Score: 0.9241)】\n“MySQL HeatWave 通过内置 DISTANCE(embedding, :query_vec) 函数支持毫秒级 Cosine 向量计算，与业务表无缝原子事务结合，杜绝异构向量数据库数据同步延时...”`
    );
  };

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-50 dark:bg-zinc-950 p-6 sm:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* 标题 */}
        <div className="flex items-center justify-between border-b border-zinc-200 dark:border-zinc-800 pb-4">
          <div>
            <h1 className="text-xl font-bold text-zinc-900 dark:text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-emerald-500" />
              RAG 知识库管理
            </h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
              基于 OCI MySQL HeatWave 原生 1536 维向量引擎，支持企业文档智能切片与高精语义检索。
            </p>
          </div>
          <button className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium transition-all shadow-sm active:scale-95">
            <UploadCloud className="w-4 h-4" />
            <span>上传新文档</span>
          </button>
        </div>

        {/* 知识库文档列表卡片 */}
        <div className="space-y-3">
          <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            已挂载文档资产 ({docs.length})
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {docs.map((doc) => (
              <div
                key={doc.id}
                className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm hover:border-zinc-300 dark:hover:border-zinc-700 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5 truncate">
                    <Database className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                    <span className="text-xs font-semibold text-zinc-800 dark:text-zinc-200 truncate">
                      {doc.title}
                    </span>
                  </div>
                  <span className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    <CheckCircle2 className="w-3 h-3" />
                    已就绪
                  </span>
                </div>

                <div className="mt-4 flex items-center justify-between text-[11px] text-zinc-500 border-t border-zinc-100 dark:border-zinc-800/60 pt-2.5">
                  <div className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5" />
                    <span>{doc.chunk_count} 个向量切片</span>
                  </div>
                  <span>类型: {doc.file_type.toUpperCase()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 向量相似度检索实验室 */}
        <div className="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm space-y-3">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-sky-500" />
            <span className="text-sm font-semibold text-zinc-900 dark:text-white">
              语义检索快速实验室 (HeatWave Retrieval Playground)
            </span>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            输入测试提问，实时测试知识库向量召回切片与余弦相似度得分。
          </p>

          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="例如：MySQL HeatWave 如何进行向量检索？"
              className="flex-1 px-3.5 py-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-sky-500"
            />
            <button
              onClick={handleTestSearch}
              className="px-4 py-2 rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-xs font-medium hover:bg-zinc-800 dark:hover:bg-zinc-100 transition-all active:scale-95"
            >
              执行检索
            </button>
          </div>

          {testResult && (
            <div className="p-3.5 rounded-xl bg-zinc-100 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap leading-relaxed">
              {testResult}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
