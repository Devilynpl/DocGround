"""Testy jednostkowe Fazy 1: Ingest, Layout-Aware Parser, zachowanie tabel i schemat metadanych."""

import pytest
from pathlib import Path
from docground.models import DocumentChunk, ChunkType
from docground.ingest.parser import LayoutAwareParser
from docground.ingest.chunker import SemanticTablePreservingChunker, create_chunk_id, generate_anchor
from docground.config import RAW_DATA_DIR


def test_document_chunk_model_validation():
    chunk = DocumentChunk(
        chunk_id="abc12345",
        doc_name="test_doc.pdf",
        doc_type="pdf",
        page_number=1,
        chunk_type=ChunkType.TABLE,
        content="| A | B |\n|---|---|\n| 1 | 2 |",
        raw_context_anchor="| A | B | ... | 1 | 2 |",
        metadata={"table_id": 1}
    )
    assert chunk.doc_name == "test_doc.pdf"
    assert chunk.chunk_type == ChunkType.TABLE
    assert chunk.page_number == 1
    assert "| A | B |" in chunk.content


def test_layout_aware_parser_finds_tables_in_financial_report():
    parser = LayoutAwareParser()
    pdf_path = RAW_DATA_DIR / "raport_finansowy_q3_2025.pdf"
    assert pdf_path.exists(), "Plik raportu finansowego powinien istnieć"

    blocks = parser.parse_pdf(pdf_path)
    assert len(blocks) > 0

    table_blocks = [b for b in blocks if b.block_type == "table"]
    assert len(table_blocks) >= 2, "W raporcie finansowym powinny zostać wykryte minimum 2 tabele"
    
    # Sprawdzenie czy w tabeli 1 występuje nagłówek i format Markdown
    t1 = table_blocks[0]
    assert "|" in t1.content
    assert "EBITDA" in t1.content or "Q1 2025" in t1.content


def test_chunker_preserves_tables_as_atomic_chunks():
    parser = LayoutAwareParser()
    chunker = SemanticTablePreservingChunker()
    pdf_path = RAW_DATA_DIR / "cennik_cloud_v2_2025.pdf"

    blocks = parser.parse_pdf(pdf_path)
    chunks = chunker.chunk_blocks(blocks)

    table_chunks = [c for c in chunks if c.chunk_type == ChunkType.TABLE]
    assert len(table_chunks) == 1
    assert "Standard Cloud VM" in table_chunks[0].content
    assert "AI Inference GPU Node" in table_chunks[0].content
    assert len(table_chunks[0].raw_context_anchor) > 10


def test_create_chunk_id_is_deterministic():
    id1 = create_chunk_id("doc.pdf", 1, "test text")
    id2 = create_chunk_id("doc.pdf", 1, "test text")
    id3 = create_chunk_id("doc.pdf", 2, "test text")
    assert id1 == id2
    assert id1 != id3
