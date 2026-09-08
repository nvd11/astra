/**
 * 知识库文档实体
 */
export interface KnowledgeDocument {
  id: string;
  title: string;
  file_type: string;
  chunk_count: number;
  status: 'indexed' | 'processing' | 'failed';
  created_at: string;
}

/**
 * 文档向量切片实体
 */
export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  score?: number;
}
