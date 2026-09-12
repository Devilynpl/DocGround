from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChunkType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    HEADER = "header"


class DocumentChunk(BaseModel):
    chunk_id: str = Field(description="Unikalny hash sha256 z treści i metadanych źródłowych")
    doc_name: str = Field(description="Nazwa pliku dokumentu, np. raport_finansowy_q3.pdf")
    doc_type: str = Field(description="Typ dokumentu, np. pdf, html, docx")
    page_number: int = Field(description="Fizyczny numer strony w dokumencie (1-indexed)")
    chunk_type: ChunkType = Field(description="Typ zawartości chunka: text, table, header")
    content: str = Field(description="Tekst chunka (w przypadku tabel: natywny Markdown)")
    raw_context_anchor: str = Field(
        description="Unikalne pierwsze i ostatnie 10 słów chunka do weryfikacji cytatu"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Dodatkowe metadane (np. tytuł sekcji, nr tabeli)")


class SourceReference(BaseModel):
    doc_name: str
    page_number: int
    quote_snippet: str
    chunk_id: Optional[str] = None
    is_verified: bool = False


class GroundedResponse(BaseModel):
    answer: str
    is_confident: bool
    sources: List[SourceReference] = Field(default_factory=list)
    latency_ms: Optional[float] = None
    retrieval_strategy: Optional[str] = None
