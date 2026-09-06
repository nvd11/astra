"""OCI MySQL HeatWave 原生向量检索存储引擎 (VECTOR(1536)).

支持基于 Cosine 距离的原生 SQL 高性能向量计算与 Python 降级检索.
"""

import json
import math
from typing import Any

from loguru import logger
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.knowledge import DocumentChunk, KnowledgeDocument


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """计算两个向量的余弦相似度 (0.0 ~ 1.0).

    Args:
        vec1: 向量 1
        vec2: 向量 2

    Returns:
        float: 余弦相似度
    """
    dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=True))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class HeatWaveVectorStore:
    """OCI MySQL HeatWave 原生向量知识库检索器."""

    def __init__(self, use_native_heatwave: bool = False) -> None:
        """初始化向量存储.

        Args:
            use_native_heatwave: 是否启用 HeatWave 原生 VECTOR 函数 (DISTANCE)
        """
        self.use_native_heatwave = use_native_heatwave

    async def add_document_with_chunks(
        self,
        session: AsyncSession,
        user_id: str,
        title: str,
        chunks_data: list[dict[str, Any]],
        file_type: str = "txt",
    ) -> KnowledgeDocument:
        """保存文档与其向量分片.

        Args:
            session: 异步数据库会话
            user_id: 用户 ID (行级隔离)
            title: 文档名称
            chunks_data: 切片列表 [{'content': '...', 'embedding': [0.1, ...], 'metadata': {}}]
            file_type: 文件后缀

        Returns:
            KnowledgeDocument: 创建的文档对象
        """
        doc = KnowledgeDocument(
            user_id=user_id,
            title=title,
            file_type=file_type,
            chunk_count=len(chunks_data),
        )
        session.add(doc)
        await session.flush()
        await session.refresh(doc)

        for idx, item in enumerate(chunks_data):
            chunk = DocumentChunk(
                document_id=doc.id,
                user_id=user_id,
                chunk_index=idx,
                content=item["content"],
                embedding_json=item["embedding"],
                chunk_metadata=item.get("metadata", {}),
            )
            session.add(chunk)

        await session.flush()
        logger.info(
            f"Added knowledge doc id={doc.id} with {len(chunks_data)} chunks for user={user_id}"
        )
        return doc

    async def similarity_search(
        self,
        session: AsyncSession,
        query_embedding: list[float],
        user_id: str,
        top_k: int = 4,
    ) -> list[dict[str, Any]]:
        """基于向量距离相似度检索最相关的切片（强制用户隔离）.

        Args:
            session: 异步数据库会话
            query_embedding: 查询向量 (如 1536 维 float 数组)
            user_id: 当前用户 ID
            top_k: 返回最相似结果数

        Returns:
            list[dict]: 包含 content, score, document_id, metadata 的列表
        """
        if self.use_native_heatwave:
            try:
                # OCI MySQL HeatWave 原生 SQL 距离检索: DISTANCE(v1, v2, 'COSINE')
                vec_str = json.dumps(query_embedding)
                sql = text(
                    """
                    SELECT id, document_id, content, metadata,
                           DISTANCE(embedding, string_to_vector(:query_vec), 'COSINE') AS distance
                    FROM document_chunks
                    WHERE user_id = :user_id
                    ORDER BY distance ASC
                    LIMIT :top_k
                    """
                )
                res = await session.execute(
                    sql, {"query_vec": vec_str, "user_id": user_id, "top_k": top_k}
                )
                rows = res.fetchall()

                return [
                    {
                        "id": row.id,
                        "document_id": row.document_id,
                        "content": row.content,
                        "metadata": row.metadata,
                        "score": round(1.0 - float(row.distance), 4),
                    }
                    for row in rows
                ]
            except Exception as heatwave_err:
                logger.warning(
                    f"HeatWave native vector query failed, falling back: {heatwave_err}"
                )

        # 降级模式：从数据库加载并计算余弦相似度 (适用于单元测试及本地开发环境)
        stmt = select(DocumentChunk).where(DocumentChunk.user_id == user_id)
        result = await session.execute(stmt)
        chunks = list(result.scalars().all())

        scored_chunks: list[tuple[float, DocumentChunk]] = []
        for c in chunks:
            sim = cosine_similarity(query_embedding, c.embedding_json)
            scored_chunks.append((sim, c))

        # 按相似度降序排序
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_chunks[:top_k]

        return [
            {
                "id": c.id,
                "document_id": c.document_id,
                "content": c.content,
                "metadata": c.chunk_metadata,
                "score": round(sim, 4),
            }
            for sim, c in top_results
        ]

    async def delete_document(
        self, session: AsyncSession, document_id: str, user_id: str
    ) -> bool:
        """删除文档及其所属切片.

        Args:
            session: 异步数据库会话
            document_id: 文档 ID
            user_id: 用户 ID

        Returns:
            bool: 是否删除成功
        """
        # 删除所有切片
        await session.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.user_id == user_id,
            )
        )
        # 删除文档
        res = await session.execute(
            delete(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.user_id == user_id,
            )
        )
        await session.flush()
        return (getattr(res, "rowcount", 0) or 0) > 0
