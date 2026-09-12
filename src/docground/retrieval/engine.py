"""Główny silnik wyszukiwania hybrydowego:
Łączy BM25 + Dense + RRF + Cross-Encoder Reranker z opcjonalnym fallbackiem / baselinem.
"""

import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from docground.models import DocumentChunk
from docground.config import CHUNKS_PATH, settings
from docground.retrieval.bm25 import BM25Retriever
from docground.retrieval.dense import DenseRetriever
from docground.retrieval.rrf import reciprocal_rank_fusion
from docground.retrieval.reranker import CrossEncoderReranker


def load_chunks(chunks_path: Path = CHUNKS_PATH) -> List[DocumentChunk]:
    chunks: List[DocumentChunk] = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(DocumentChunk.model_validate_json(line))
    return chunks


class HybridSearchEngine:
    def __init__(self, chunks: Optional[List[DocumentChunk]] = None):
        self.chunks = chunks or load_chunks()
        self.bm25 = BM25Retriever(self.chunks)
        self.dense = DenseRetriever(self.chunks, model_name=settings.dense_model_name)
        self.reranker = CrossEncoderReranker(model_name=settings.reranker_model_name)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        use_reranker: bool = True
    ) -> Tuple[List[Tuple[DocumentChunk, float]], bool]:
        """Wykonuje pełny potok hybrydowy (BM25 + Dense -> RRF -> Reranker)."""
        # 1. Sparse BM25 (top 20)
        bm25_res = self.bm25.search(query, top_k=settings.bm25_top_k)

        # 2. Dense Vector (top 20)
        dense_res = self.dense.search(query, top_k=settings.dense_top_k, filters=filters)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_res = reciprocal_rank_fusion(
            dense_results=dense_res,
            sparse_results=bm25_res,
            k=settings.rrf_k,
            top_k=20
        )

        candidates = [ch for ch, _ in rrf_res]

        if not use_reranker:
            return rrf_res[:top_k], False

        # 4. Cross-Encoder Reranker
        reranked_res, is_low_confidence = self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=top_k,
            threshold=settings.rejection_threshold
        )

        return reranked_res, is_low_confidence
