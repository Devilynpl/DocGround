import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent

try:
    from dotenv import load_dotenv
    # Ładowanie zmiennych środowiskowych z pliku DocGround/.env lub nadrzędnego .env
    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BASE_DIR.parent / ".env")
except ImportError:
    pass

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CHUNKS_PATH = PROCESSED_DATA_DIR / "chunks.jsonl"
EVALS_DIR = BASE_DIR / "tests" / "evals"
GOLDEN_SET_PATH = EVALS_DIR / "golden_set.json"


class Settings(BaseModel):
    dense_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model_name: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    bm25_top_k: int = 20
    dense_top_k: int = 20
    rrf_k: int = 60
    final_top_k: int = 5
    rejection_threshold: float = 0.20
    chunk_size: int = 500
    chunk_overlap: int = 90
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model_name: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


settings = Settings()
