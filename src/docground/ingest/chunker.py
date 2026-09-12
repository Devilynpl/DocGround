"""Semantyczny chunker zachowujący nienaruszone tabele Markdown i tworzący DocumentChunk z kotwicą raw_context_anchor."""

import hashlib
import json
from pathlib import Path
from typing import List
from docground.models import DocumentChunk, ChunkType
from docground.ingest.parser import RawBlock, LayoutAwareParser
from docground.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, CHUNKS_PATH, settings


def generate_anchor(text: str) -> str:
    """Tworzy raw_context_anchor składający się z pierwszych i ostatnich słów tekstu."""
    words = text.strip().split()
    if len(words) <= 15:
        return text.strip()
    first_part = " ".join(words[:8])
    last_part = " ".join(words[-8:])
    return f"{first_part} ... {last_part}"


def create_chunk_id(doc_name: str, page_number: int, content: str) -> str:
    hasher = hashlib.sha256()
    hasher.update(f"{doc_name}::{page_number}::{content.strip()}".encode("utf-8"))
    return hasher.hexdigest()[:16]


class SemanticTablePreservingChunker:
    def __init__(self, max_tokens: int = 500, overlap_tokens: int = 90):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def _estimate_tokens(self, text: str) -> int:
        return len(text.split())

    def chunk_blocks(self, blocks: List[RawBlock]) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []

        for block in blocks:
            # 1. TABELE: Nigdy nie dzielimy tabeli w połowie, cała tabela to pojedynczy atomowy chunk
            if block.block_type == "table":
                cid = create_chunk_id(block.doc_name, block.page_number, block.content)
                chunks.append(
                    DocumentChunk(
                        chunk_id=cid,
                        doc_name=block.doc_name,
                        doc_type=block.doc_type,
                        page_number=block.page_number,
                        chunk_type=ChunkType.TABLE,
                        content=block.content,
                        raw_context_anchor=generate_anchor(block.content),
                        metadata=block.metadata
                    )
                )
                continue

            # 2. TEKST / HEADER: Rekurencyjne lub akapitowe dzielenie z oknem i nakładaniem
            text = block.content.strip()
            words = text.split()
            token_count = len(words)

            if token_count <= self.max_tokens:
                cid = create_chunk_id(block.doc_name, block.page_number, text)
                chunks.append(
                    DocumentChunk(
                        chunk_id=cid,
                        doc_name=block.doc_name,
                        doc_type=block.doc_type,
                        page_number=block.page_number,
                        chunk_type=ChunkType.HEADER if block.block_type == "header" else ChunkType.TEXT,
                        content=text,
                        raw_context_anchor=generate_anchor(text),
                        metadata=block.metadata
                    )
                )
            else:
                # Dzielenie z overlapem
                step = self.max_tokens - self.overlap_tokens
                for i in range(0, token_count, step):
                    window_words = words[i:i + self.max_tokens]
                    window_text = " ".join(window_words)
                    cid = create_chunk_id(block.doc_name, block.page_number, window_text)
                    chunks.append(
                        DocumentChunk(
                            chunk_id=cid,
                            doc_name=block.doc_name,
                            doc_type=block.doc_type,
                            page_number=block.page_number,
                            chunk_type=ChunkType.TEXT,
                            content=window_text,
                            raw_context_anchor=generate_anchor(window_text),
                            metadata={**block.metadata, "window_index": i // step}
                        )
                    )
                    if i + self.max_tokens >= token_count:
                        break

        return chunks


def process_and_index_corpus(raw_dir: Path = RAW_DATA_DIR, output_file: Path = CHUNKS_PATH) -> List[DocumentChunk]:
    parser = LayoutAwareParser()
    chunker = SemanticTablePreservingChunker(
        max_tokens=settings.chunk_size,
        overlap_tokens=settings.chunk_overlap
    )

    all_chunks: List[DocumentChunk] = []
    pdf_files = list(raw_dir.glob("*.pdf"))

    for pdf_path in pdf_files:
        blocks = parser.parse_pdf(pdf_path)
        chunks = chunker.chunk_blocks(blocks)
        all_chunks.extend(chunks)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for ch in all_chunks:
            f.write(ch.model_dump_json() + "\n")

    print(f"Zindeksowano {len(all_chunks)} chunków z {len(pdf_files)} dokumentów do {output_file}")
    return all_chunks


if __name__ == "__main__":
    process_and_index_corpus()
