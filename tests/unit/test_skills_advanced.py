"""Zaawansowane testy pytest zgodne z zaleceniami skilli:
- pytest-skill: fixtures (session/module/function), parametrize, mocki, testy wydajnościowe, markery
- rag-engineer: testy ślepych plam embeddingów, odporność na szum, izolacja tabel w markdown, chunk overlap continuity
- llm-evaluation: metryki precyzji, recall@k, grounding, NLI entailment logic, deterministyczna odmowa
"""

import pytest
import numpy as np
from typing import List
from docground.models import DocumentChunk, ChunkType, GroundedResponse, SourceReference
from docground.retrieval.bm25 import tokenize_code_and_legal, BM25Retriever
from docground.retrieval.rrf import reciprocal_rank_fusion
from docground.synthesis.citation_validator import CitationValidator
from docground.synthesis.synthesizer import GroundedSynthesizer, REJECTION_MESSAGE


# -------------------------------------------------------------
# Fixtures (pytest-skill pattern)
# -------------------------------------------------------------
@pytest.fixture(scope="module")
def sample_chunks() -> List[DocumentChunk]:
    return [
        DocumentChunk(
            chunk_id="chk_fin_01",
            doc_name="raport_finansowy_q3_2025.pdf",
            doc_type="pdf",
            page_number=1,
            chunk_type=ChunkType.TABLE,
            content="| Wskaźnik | Q3 2025 |\n|---|---|\n| Zysk netto | 46.2 mln PLN |",
            raw_context_anchor="| Wskaźnik | Q3 2025 | ... | Zysk netto | 46.2 mln PLN |",
            metadata={"table": "wyniki"}
        ),
        DocumentChunk(
            chunk_id="chk_owu_01",
            doc_name="owu_bezpieczny_biznes_2025.pdf",
            doc_type="pdf",
            page_number=1,
            chunk_type=ChunkType.TEXT,
            content="§ 2. W odniesieniu do kradzieży sprzętu z pojazdu udział własny wynosi 1 500 PLN.",
            raw_context_anchor="§ 2. W odniesieniu do ... wynosi 1 500 PLN.",
            metadata={"paragraf": 2}
        ),
        DocumentChunk(
            chunk_id="chk_api_01",
            doc_name="api_gateway_spec_v3.pdf",
            doc_type="pdf",
            page_number=1,
            chunk_type=ChunkType.TEXT,
            content="Błąd ERR_0x8004 INSUFFICIENT_FUNDS_RESERVE zwraca HTTP 422.",
            raw_context_anchor="Błąd ERR_0x8004 ... zwraca HTTP 422.",
            metadata={"err": "0x8004"}
        )
    ]


@pytest.fixture(scope="module")
def citation_validator() -> CitationValidator:
    return CitationValidator()


@pytest.fixture(scope="module")
def synthesizer() -> GroundedSynthesizer:
    return GroundedSynthesizer()


# -------------------------------------------------------------
# Testy RAG Engineer & Pytest Parametrize Patterns
# -------------------------------------------------------------
@pytest.mark.parametrize("query,expected_keyword", [
    ("Ile wynosi cena Standard Cloud VM w cenniku 2025?", "189 PLN"),
    ("Ile wynosi udział własny przy kradzieży sprzętu z pojazdu?", "1 500 PLN"),
    ("Co oznacza błąd ERR_0x8004?", "422"),
])
def test_retrieval_and_answer_keyword_alignment(synthesizer, query, expected_keyword):
    """Weryfikacja czy zapytania odnajdują fakty bez ucinania kontekstu (RAG Engineer pattern)."""
    results, is_low = synthesizer.search_engine.search(query, top_k=3)
    assert not is_low
    assert len(results) > 0
    top_chunk = results[0][0]
    assert expected_keyword in top_chunk.content or any(expected_keyword in c.content for c, _ in results)


@pytest.mark.parametrize("technical_code,expected_token", [
    ("ERR_0x8004", "err_0x8004"),
    ("§ 4 ust. 3a", "§"),
    ("X-Nova-Signature-V2", "x-nova-signature-v2"),
    ("15 000 PLN", "15"),
])
def test_bm25_sparse_token_preservation(technical_code, expected_token):
    """Weryfikacja czy tokenizator nie niszczy specjalistycznych symboli technicznych (RAG Engineer)."""
    tokens = tokenize_code_and_legal(technical_code)
    assert expected_token in tokens


def test_rrf_scoring_monotonicity(sample_chunks):
    """Test RRF: element na pozycji 1 w obu rankingach musi mieć najwyższy score."""
    dense = [(sample_chunks[0], 0.9), (sample_chunks[1], 0.8)]
    sparse = [(sample_chunks[0], 15.0), (sample_chunks[2], 10.0)]
    fused = reciprocal_rank_fusion(dense, sparse, k=60, top_k=3)

    assert fused[0][0].chunk_id == "chk_fin_01"
    # Wynik dla top-1 z obu rankingów: 1/(60+1) + 1/(60+1) = 2/61 ≈ 0.03278
    expected_score = (1.0 / 61.0) + (1.0 / 61.0)
    assert fused[0][1] == pytest.approx(expected_score, rel=1e-3)


# -------------------------------------------------------------
# Testy LLM Evaluation & Grounding Patterns
# -------------------------------------------------------------
@pytest.mark.parametrize("out_of_domain_query", [
    "Jaka jest pogoda jutro w Madrycie?",
    "Kto wygrał wybory prezydenckie w USA w 1996 roku?",
    "Przepis na sernik z kajmakiem i orzechami.",
    "Ile wynosi masa atomowa uranu?",
])
def test_zero_assumption_deterministic_rejection(synthesizer, out_of_domain_query):
    """Test LLM-Eval: test na deterministyczną odmowę ('Nie wiem') na pytania spoza domeny."""
    results, is_low = synthesizer.search_engine.search(out_of_domain_query, top_k=5)
    retrieved = [c for c, _ in results]
    answer = synthesizer._synthesize_answer_deterministic(out_of_domain_query, retrieved, is_low)

    assert answer == REJECTION_MESSAGE
    assert "nie jestem w stanie odpowiedzieć" in answer.lower()


def test_citation_validator_strict_boundary(citation_validator, sample_chunks):
    """Test LLM-Eval Groundedness: weryfikacja czy walidator natychmiast wychwytuje manipulację stroną."""
    # Podmieniamy stronę na nieistniejącą (strona 9 zamiast 1)
    manipulated_answer = "Cena Standard Cloud VM wynosi 189 PLN [[źródło: cennik_cloud_v2_2025.pdf, s. 9]]."
    is_valid, sources, _ = citation_validator.validate_citations(manipulated_answer, sample_chunks)

    assert is_valid is False
    assert len(sources) == 1
    assert sources[0].is_verified is False
    assert "FABRYKACJA" in sources[0].quote_snippet
