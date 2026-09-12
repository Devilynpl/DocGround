"""Testy jednostkowe Fazy 4: Synteza z restrykcyjnymi cytowaniami, Citation Validator i GroundedResponse."""

import pytest
import asyncio
from docground.models import DocumentChunk, ChunkType, GroundedResponse
from docground.synthesis.citation_validator import CitationValidator
from docground.synthesis.synthesizer import GroundedSynthesizer, REJECTION_MESSAGE


def test_citation_validator_extracts_and_verifies_correctly():
    validator = CitationValidator()
    text = "Zysk wyniósł 46.2 mln PLN [[źródło: raport.pdf, s. 1]] oraz marża 20% [[źródło: cennik.pdf, s. 2]]."
    
    chunks = [
        DocumentChunk(chunk_id="1", doc_name="raport.pdf", doc_type="pdf", page_number=1, chunk_type=ChunkType.TEXT, content="Zysk", raw_context_anchor="Zysk"),
        DocumentChunk(chunk_id="2", doc_name="cennik.pdf", doc_type="pdf", page_number=2, chunk_type=ChunkType.TEXT, content="Marża", raw_context_anchor="Marża"),
    ]

    is_valid, sources, _ = validator.validate_citations(text, chunks)
    assert is_valid is True
    assert len(sources) == 2
    assert sources[0].doc_name == "raport.pdf"
    assert sources[0].page_number == 1
    assert sources[0].is_verified is True


def test_citation_validator_detects_fabricated_citations():
    validator = CitationValidator()
    text = "Fakt zmyślony [[źródło: falszywy_plik.pdf, s. 99]]."
    chunks = [
        DocumentChunk(chunk_id="1", doc_name="raport.pdf", doc_type="pdf", page_number=1, chunk_type=ChunkType.TEXT, content="X", raw_context_anchor="X")
    ]

    is_valid, sources, _ = validator.validate_citations(text, chunks)
    assert is_valid is False
    assert len(sources) == 1
    assert sources[0].is_verified is False
    assert "FABRYKACJA" in sources[0].quote_snippet


@pytest.mark.asyncio
async def test_grounded_synthesizer_streaming_and_rejection():
    synthesizer = GroundedSynthesizer()

    # 1. Test pytania out-of-domain (wymuszone deterministyczne 'Nie wiem')
    stream_ood = synthesizer.generate_response_stream("Ile bramek strzelił Robert Lewandowski?")
    tokens_ood = []
    final_resp_ood = None

    async for chunk in stream_ood:
        if chunk["type"] == "token":
            tokens_ood.append(chunk["content"])
        elif chunk["type"] == "final_response":
            final_resp_ood = chunk["payload"]

    full_text_ood = "".join(tokens_ood).strip()
    assert full_text_ood == REJECTION_MESSAGE
    assert final_resp_ood.is_confident is False
    assert len(final_resp_ood.sources) == 0

    # 2. Test pytania ze znajomością kontekstu (np. cennik Cloud VM)
    stream_valid = synthesizer.generate_response_stream("Ile wynosi cena Standard Cloud VM w cenniku 2025?")
    tokens_valid = []
    final_resp_valid = None

    async for chunk in stream_valid:
        if chunk["type"] == "token":
            tokens_valid.append(chunk["content"])
        elif chunk["type"] == "final_response":
            final_resp_valid = chunk["payload"]

    full_text_valid = "".join(tokens_valid).strip()
    assert "189" in full_text_valid
    assert "[[źródło: cennik_cloud_v2_2025.pdf, s. 1]]" in full_text_valid
    assert final_resp_valid.is_confident is True
    assert len(final_resp_valid.sources) > 0
    assert final_resp_valid.sources[0].is_verified is True
