import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CHUNKS_PATH = PROCESSED_DATA_DIR / "chunks.jsonl"
EVALS_DIR = BASE_DIR / "tests" / "evals"
GOLDEN_SET_PATH = EVALS_DIR / "golden_set.json"


class Settings(BaseModel):
    dense_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    bm25_top_k: int = 20
    dense_top_k: int = 20
    rrf_k: int = 60
    final_top_k: int = 5
    rejection_threshold: float = 0.20
    chunk_size: int = 500
    chunk_overlap: int = 90


settings = Settings()
