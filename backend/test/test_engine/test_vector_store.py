"""OCI MySQL HeatWave 向量检索引擎单元测试."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.engine.vector_store import HeatWaveVectorStore, cosine_similarity
from src.models.knowledge import DocumentChunk


class TestVectorStore:
    """向量检索存储测试类."""

    def test_cosine_similarity(self):
        """测试余弦相似度计算."""
        # 完全相同向量
        assert round(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 4) == 1.0
        # 正交向量
        assert round(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 4) == 0.0
        # 零向量
        assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0

    @pytest.mark.asyncio
    async def test_add_document_with_chunks(self):
        """测试添加文档与向量分片."""
        store = HeatWaveVectorStore(use_native_heatwave=False)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        chunks = [
            {
                "content": "切片一",
                "embedding": [0.1, 0.2, 0.3],
                "metadata": {"page": 1},
            },
            {
                "content": "切片二",
                "embedding": [0.4, 0.5, 0.6],
                "metadata": {"page": 2},
            },
        ]

        doc = await store.add_document_with_chunks(
            session=mock_session,
            user_id="user-123",
            title="员工手册.pdf",
            chunks_data=chunks,
            file_type="pdf",
        )

        assert doc.user_id == "user-123"
        assert doc.title == "员工手册.pdf"
        assert doc.chunk_count == 2
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_similarity_search_fallback(self):
        """测试相似度检索 (Python 降级计算模式)."""
        store = HeatWaveVectorStore(use_native_heatwave=False)
        mock_session = AsyncMock(spec=AsyncSession)

        c1 = DocumentChunk(
            id="c1",
            document_id="d1",
            user_id="user-123",
            chunk_index=0,
            content="高相似度切片",
            embedding_json=[1.0, 0.0, 0.0],
            chunk_metadata={"tag": "high"},
        )
        c2 = DocumentChunk(
            id="c2",
            document_id="d1",
            user_id="user-123",
            chunk_index=1,
            content="低相似度切片",
            embedding_json=[0.0, 1.0, 0.0],
            chunk_metadata={"tag": "low"},
        )

        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = [c1, c2]
        mock_session.execute.return_value = mock_res

        query_vec = [1.0, 0.0, 0.0]
        results = await store.similarity_search(
            mock_session, query_vec, "user-123", top_k=1
        )

        assert len(results) == 1
        assert results[0]["id"] == "c1"
        assert results[0]["score"] == 1.0
        assert results[0]["content"] == "高相似度切片"

    @pytest.mark.asyncio
    async def test_similarity_search_native_heatwave_success(self):
        """测试 OCI MySQL HeatWave 原生 SQL 距离检索."""
        store = HeatWaveVectorStore(use_native_heatwave=True)
        mock_session = AsyncMock(spec=AsyncSession)

        mock_row = MagicMock()
        mock_row.id = "c1"
        mock_row.document_id = "d1"
        mock_row.content = "HeatWave 原生切片"
        mock_row.metadata = {"source": "heatwave"}
        mock_row.distance = 0.15

        mock_res = MagicMock()
        mock_res.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_res

        results = await store.similarity_search(
            mock_session, [0.1, 0.2], "user-123", top_k=5
        )

        assert len(results) == 1
        assert results[0]["id"] == "c1"
        assert results[0]["score"] == 0.85
        assert results[0]["content"] == "HeatWave 原生切片"

    @pytest.mark.asyncio
    async def test_similarity_search_native_heatwave_error_fallback(self):
        """测试 HeatWave 原生检索出错时自动平滑降级."""
        store = HeatWaveVectorStore(use_native_heatwave=True)
        mock_session = AsyncMock(spec=AsyncSession)

        c1 = DocumentChunk(
            id="c1",
            document_id="d1",
            user_id="user-123",
            chunk_index=0,
            content="降级切片",
            embedding_json=[1.0, 0.0],
            chunk_metadata={},
        )

        mock_fallback_res = MagicMock()
        mock_fallback_res.scalars.return_value.all.return_value = [c1]

        # 第一次执行原生 SQL 抛异常，第二次降级执行成功
        mock_session.execute.side_effect = [
            RuntimeError("HeatWave VECTOR plugin not loaded"),
            mock_fallback_res,
        ]

        results = await store.similarity_search(mock_session, [1.0, 0.0], "user-123")
        assert len(results) == 1
        assert results[0]["id"] == "c1"
        assert results[0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_delete_document(self):
        """测试删除知识库文档."""
        store = HeatWaveVectorStore()
        mock_session = AsyncMock(spec=AsyncSession)

        mock_del_doc_res = MagicMock()
        mock_del_doc_res.rowcount = 1
        mock_session.execute.side_effect = [MagicMock(), mock_del_doc_res]

        ok = await store.delete_document(mock_session, "doc-1", "user-123")
        assert ok is True
        assert mock_session.execute.call_count == 2
