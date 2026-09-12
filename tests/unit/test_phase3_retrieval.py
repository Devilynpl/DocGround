"""Testy jednostkowe Fazy 3: BM25, Dense, RRF i Cross-Encoder Reranker."""

import pytest
from docground.models import DocumentChunk, ChunkType
from docground.retrieval.bm25 import BM25Retriever, tokenize_code_and_legal
from docground.retrieval.rrf import reciprocal_rank_fusion
from docground.retrieval.engine import load_chunks, HybridSearchEngine


def test_tokenize_code_and_legal():
    tokens = tokenize_code_and_legal("Błąd ERR_0x8004 oraz art. § 14 ust. 2b!")
    assert "err_0x8004" in tokens
    assert "§" in tokens or "14" in tokens
    assert "błąd" in tokens


def test_reciprocal_rank_fusion_logic():
    ch1 = DocumentChunk(chunk_id="c1", doc_name="d1.pdf", doc_type="pdf", page_number=1, chunk_type=ChunkType.TEXT, content="a", raw_context_anchor="a")
    ch2 = DocumentChunk(chunk_id="c2", doc_name="d2.pdf", doc_type="pdf", page_number=1, chunk_type=ChunkType.TEXT, content="b", raw_context_anchor="b")
    ch3 = DocumentChunk(chunk_id="c3", doc_name="d3.pdf", doc_type="pdf", page_number=1, chunk_type=ChunkType.TEXT, content="c", raw_context_anchor="c")

    dense_res = [(ch1, 0.9), (ch2, 0.8)]
    sparse_res = [(ch2, 10.0), (ch3, 5.0)]

    fused = reciprocal_rank_fusion(dense_res, sparse_res, k=60, top_k=3)
    # ch2 występuje w obu rankingach, więc powinien mieć najwyższy wynik RRF
    assert fused[0][0].chunk_id == "c2"
    assert len(fused) == 3


def test_hybrid_search_engine_initialization_and_search():
    engine = HybridSearchEngine()
    assert len(engine.chunks) > 0

    results, is_low = engine.search("Ile wynosi cena Standard Cloud VM?", top_k=3)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "cennik_cloud" in top_chunk.doc_name
    assert is_low is False
