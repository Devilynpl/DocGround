"""Cross-Encoder Reranker z dynamicznym progiem odrzucenia (Rejection Threshold).
Zapewnia głębokie dopasowanie par (query, chunk_content) i odcina losowy szum.
"""

from typing import List, Tuple
from sentence_transformers import CrossEncoder
from docground.models import DocumentChunk
from docground.config import settings


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        print(f"[CrossEncoderReranker] Ładowanie modelu rerankera: {model_name}...")
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        candidates: List[DocumentChunk],
        top_k: int = 5,
        threshold: float = 0.20
    ) -> Tuple[List[Tuple[DocumentChunk, float]], bool]:
        """Rerankuje kandydatów i zwraca (top_k_chunks, is_low_confidence)."""
        if not candidates:
            return [], True

        pairs = [[query, f"Dokument: {c.doc_name}, Strona: {c.page_number}. Treść: {c.content}"] for c in candidates]
        raw_scores = self.model.predict(pairs)

        # Normalizacja logitów do zakresu (0, 1) za pomocą funkcji sigmoid
        import numpy as np
        scores = 1.0 / (1.0 + np.exp(-raw_scores))

        scored_candidates = list(zip(candidates, [float(s) for s in scores]))
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        top_results = scored_candidates[:top_k]

        # Weryfikacja progu odrzucenia
        highest_score = top_results[0][1] if top_results else 0.0
        is_low_confidence = highest_score < threshold

        return top_results, is_low_confidence
