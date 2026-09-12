"""Testy jednostkowe Fazy 2: Eval-First, Golden Set, Metryki i Walidator."""

import pytest
import json
from docground.config import GOLDEN_SET_PATH
from docground.evals.metrics import (
    EvalQuery,
    RetrievalResult,
    calculate_retrieval_recall,
    calculate_citation_precision,
    calculate_faithfulness
)


def test_golden_set_structure_and_balance():
    assert GOLDEN_SET_PATH.exists(), "Plik golden_set.json musi istnieć"
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) >= 40, "Golden Set musi mieć minimum 40 pytań"
    assert len(data) <= 60, "Golden Set mieści się w przedziale 40-60 pytań"

    # Sprawdzenie kategorii
    categories = [item["category"] for item in data]
    assert categories.count("table_qa") >= 12, "Min 12 pytań Table QA"
    assert categories.count("cross_lingual") >= 8, "Min 8 pytań Cross-Lingual"
    assert categories.count("temporal") >= 10, "Min 10 pytań Temporal"
    assert categories.count("unanswerable") >= 10, "Min 10 pytań Out-of-Domain"

    # Wymóg min. 20% pytań nieodpowiadalnych
    unanswerable_ratio = categories.count("unanswerable") / len(data)
    assert unanswerable_ratio >= 0.20, f"Pytania nieodpowiadalne stanowią {unanswerable_ratio*100:.1f}%, min to 20%"


def test_calculate_retrieval_recall_metric():
    retrieved = [
        RetrievalResult(chunk_id="1", doc_name="doc_a.pdf", page_number=1, score=0.9, content="txt"),
        RetrievalResult(chunk_id="2", doc_name="raport_finansowy_q3_2025.pdf", page_number=1, score=0.8, content="txt"),
        RetrievalResult(chunk_id="3", doc_name="doc_c.pdf", page_number=2, score=0.7, content="txt"),
    ]

    # Trafienie w top-2
    assert calculate_retrieval_recall("raport_finansowy_q3_2025.pdf", 1, retrieved, k=2) is True
    # Brak trafienia przy k=1
    assert calculate_retrieval_recall("raport_finansowy_q3_2025.pdf", 1, retrieved, k=1) is False
    # Zła strona
    assert calculate_retrieval_recall("raport_finansowy_q3_2025.pdf", 2, retrieved, k=3) is False


def test_calculate_citation_precision_metric():
    retrieved = [
        RetrievalResult(chunk_id="1", doc_name="cennik_v2.pdf", page_number=1, score=0.9, content="txt"),
        RetrievalResult(chunk_id="2", doc_name="owu.pdf", page_number=2, score=0.8, content="txt"),
    ]

    # Wszystkie cytaty poprawne
    cits_valid = [
        {"doc_name": "cennik_v2.pdf", "page_number": 1},
        {"doc_name": "owu.pdf", "page_number": 2}
    ]
    assert calculate_citation_precision(cits_valid, retrieved) == 1.0

    # 1 poprawny, 1 zmyślony
    cits_mixed = [
        {"doc_name": "cennik_v2.pdf", "page_number": 1},
        {"doc_name": "fake_doc.pdf", "page_number": 99}
    ]
    assert calculate_citation_precision(cits_mixed, retrieved) == 0.5
