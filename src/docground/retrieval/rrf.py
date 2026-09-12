r"""Reciprocal Rank Fusion (RRF) łączący wyniki Dense i Sparse (BM25):
RRF_Score(d) = \sum_{m \in M} \frac{1}{k + rank_m(d)}, gdzie k = 60
"""

from typing import List, Tuple, Dict
from docground.models import DocumentChunk


def reciprocal_rank_fusion(
    dense_results: List[Tuple[DocumentChunk, float]],
    sparse_results: List[Tuple[DocumentChunk, float]],
    k: int = 60,
    top_k: int = 20
) -> List[Tuple[DocumentChunk, float]]:
    """Łączy dwa rankingi za pomocą RRF."""
    rrf_scores: Dict[str, float] = {}
    chunk_map: Dict[str, DocumentChunk] = {}

    # Ranking z Dense
    for rank, (chunk, _) in enumerate(dense_results, start=1):
        cid = chunk.chunk_id
        chunk_map[cid] = chunk
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank))

    # Ranking ze Sparse (BM25)
    for rank, (chunk, _) in enumerate(sparse_results, start=1):
        cid = chunk.chunk_id
        chunk_map[cid] = chunk
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank))

    # Sortowanie wg połączonego wyniku RRF
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    return [(chunk_map[cid], score) for cid, score in sorted_items]
