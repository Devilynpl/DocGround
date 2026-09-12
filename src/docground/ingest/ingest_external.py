"""CLI and utility to ingest external research PDFs from dataset/ into DocGround corpus.

Extracts text and tables via LayoutAwareParser, chunks with SemanticTablePreservingChunker,
and merges into data/processed/chunks.jsonl so DocGround's HybridSearchEngine immediately
indexes both enterprise docs and research papers.
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent.parent
DOCGROUND_SRC = ROOT / "DocGround" / "src"
if str(DOCGROUND_SRC) not in sys.path:
    sys.path.insert(0, str(DOCGROUND_SRC))

from docground.config import RAW_DATA_DIR, CHUNKS_PATH, settings
from docground.ingest.parser import LayoutAwareParser
from docground.ingest.chunker import SemanticTablePreservingChunker
from docground.models import DocumentChunk


def ingest_dataset(
    dataset_dir: Path,
    output_chunks_file: Path = CHUNKS_PATH,
    copy_to_raw: bool = False,
    max_pages_per_pdf: int = 15,
) -> int:
    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        print(f"[ERROR] Dataset directory not found: {dataset_dir.resolve()}")
        return 0

    pdf_files = list(dataset_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[WARN] No PDF files found in {dataset_dir}")
        return 0

    print(f"Found {len(pdf_files)} PDF research papers in: {dataset_dir.resolve()}")

    parser = LayoutAwareParser()
    chunker = SemanticTablePreservingChunker(
        max_tokens=settings.chunk_size,
        overlap_tokens=settings.chunk_overlap,
    )

    # 1. Load existing chunks if present so we append rather than wipe
    existing_chunks: List[DocumentChunk] = []
    if output_chunks_file.exists():
        with open(output_chunks_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        existing_chunks.append(DocumentChunk.model_validate_json(line))
                    except Exception:
                        pass
        print(f"Existing corpus has {len(existing_chunks)} chunks.")

    new_chunks: List[DocumentChunk] = []
    seen_chunk_ids = {ch.chunk_id for ch in existing_chunks}

    for idx, pdf_path in enumerate(pdf_files, start=1):
        print(f"[{idx}/{len(pdf_files)}] Parsing layout: {pdf_path.name}...")
        if copy_to_raw:
            dest = RAW_DATA_DIR / pdf_path.name
            if not dest.exists():
                shutil.copy2(pdf_path, dest)

        try:
            # Parse blocks
            blocks = parser.parse_pdf(pdf_path)
            # Filter pages if requested
            if max_pages_per_pdf > 0:
                blocks = [b for b in blocks if b.page_number <= max_pages_per_pdf]

            chunks = chunker.chunk_blocks(blocks)
            added_for_file = 0
            for ch in chunks:
                if ch.chunk_id not in seen_chunk_ids:
                    new_chunks.append(ch)
                    seen_chunk_ids.add(ch.chunk_id)
                    added_for_file += 1
            print(f"  -> Generated {len(chunks)} chunks ({added_for_file} new)")
        except Exception as e:
            print(f"  [ERROR] Failed to process {pdf_path.name}: {e}")

    total_chunks = existing_chunks + new_chunks
    output_chunks_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_chunks_file, "w", encoding="utf-8") as f:
        for ch in total_chunks:
            f.write(ch.model_dump_json() + "\n")

    print("=" * 60)
    print(f"[SUCCESS] Ingest complete! Added {len(new_chunks)} new chunks from research papers.")
    print(f"Total indexed chunks in DocGround: {len(total_chunks)}")
    print(f"Index destination: {output_chunks_file.resolve()}")
    print("=" * 60)
    return len(new_chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest external PDFs into DocGround corpus.")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="dataset",
        help="Path to directory containing PDF research papers.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Max pages per document to index for benchmark performance (default: 10).",
    )
    args = parser.parse_args()

    ingest_dataset(
        dataset_dir=Path(args.dataset_dir),
        max_pages_per_pdf=args.max_pages,
    )
