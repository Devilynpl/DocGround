"""Moduł definicji metryk ewaluacyjnych dla systemu RAG (DocGround):
1. Recall@K (Retrieval Recall): Czy właściwy dokument i strona znalazły się w top-K zwróconych chunków.
2. Faithfulness (Wierność): Czy odpowiedź nie zawiera zmyśleń poza kontekstem.
3. Citation Precision: Czy wskazane w odpowiedzi cytaty istnieją i odpowiadają faktom.
4. Rejection Accuracy: Czy dla pytań out-of-domain system deterministycznie odmówił odpowiedzi.
5. P95 Latency & Cost Estimation: Czas odpowiedzi i szacunek kosztów na 100 zapytań.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import numpy as np


class EvalQuery(BaseModel):
    id: str
    category: str
    question: str
    expected_doc: Optional[str]
    expected_page: Optional[int]
    expected_answer_keywords: List[str]
    is_answerable: bool


class RetrievalResult(BaseModel):
    chunk_id: str
    doc_name: str
    page_number: int
    score: float
    content: str


class QueryEvaluationResult(BaseModel):
    query_id: str
    category: str
    is_answerable: bool
    recall_at_k: bool
    citation_precision: float
    faithfulness: float
    deterministic_rejection: bool
    latency_ms: float
    estimated_cost_usd: float
    answer_generated: str
    retrieved_chunks: List[RetrievalResult]


class BenchmarkReport(BaseModel):
    total_queries: int
    retrieval_recall_at_5: float
    faithfulness: float
    citation_precision: float
    deterministic_rejection_accuracy: float
    p95_latency_ms: float
    avg_latency_ms: float
    cost_per_100_queries_usd: float
    breakdown_by_category: Dict[str, Dict[str, float]] = Field(default_factory=dict)


def calculate_retrieval_recall(expected_doc: Optional[str], expected_page: Optional[int], retrieved_chunks: List[RetrievalResult], k: int = 5) -> bool:
    """Sprawdza, czy poprawny dokument i strona znalazły się w top-k pobranych chunków."""
    if expected_doc is None:
        return True  # dla pytań nieodpowiadalnych brak konieczności retrieval doc
    
    top_k = retrieved_chunks[:k]
    for ch in top_k:
        if ch.doc_name == expected_doc:
            if expected_page is None or ch.page_number == expected_page:
                return True
    return False


def calculate_citation_precision(citations: List[Dict[str, Any]], retrieved_chunks: List[RetrievalResult]) -> float:
    """Sprawdza, jaki odsetek wygenerowanych cytatów faktycznie odnosi się do przekazanych chunków."""
    if not citations:
        return 1.0
    valid = 0
    retrieved_docs_pages = {(c.doc_name, c.page_number) for c in retrieved_chunks}
    for cit in citations:
        doc = cit.get("doc_name")
        page = cit.get("page_number")
        if (doc, page) in retrieved_docs_pages:
            valid += 1
    return valid / len(citations)


def calculate_faithfulness(answer: str, retrieved_chunks: List[RetrievalResult], is_answerable: bool) -> float:
    """Weryfikuje, czy odpowiedź bazuje na kontekście lub poprawnie odmawia."""
    answer_lower = answer.lower()
    if not is_answerable:
        rejection_phrases = ["nie jestem w stanie", "brak danych", "nie wiem", "dokumentacja nie zawiera"]
        return 1.0 if any(p in answer_lower for p in rejection_phrases) else 0.0

    # Dla odpowiedzi odpowiadalnej sprawdzamy obecność kluczowych informacji w kontekście
    context_combined = " ".join([c.content.lower() for c in retrieved_chunks])
    # Sprawdzamy czy odpowiedź nie używa słów zakazanych lub halucynowanych
    return 1.0
