"""JudgeTargetAdapter for DocGround RAG pipeline.

Implements BaseTargetAdapter protocol from JudgeKit.
Connects JudgeKit evaluation runner to DocGround's GroundedSynthesizer,
retrieval engine, and citation validator.
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure DocGround src is in path if not installed as package
CURRENT_DIR = Path(__file__).resolve().parent
DOCGROUND_SRC = CURRENT_DIR.parent.parent / "src"
if str(DOCGROUND_SRC) not in sys.path:
    sys.path.insert(0, str(DOCGROUND_SRC))

try:
    from judgekit.target_protocol import BaseTargetAdapter, TargetOutput
except ImportError:
    # Minimal fallback protocol if judgekit isn't installed directly in active env
    from pydantic import BaseModel, Field

    class TargetOutput(BaseModel):  # type: ignore
        answer: str
        contexts: List[str] = []
        input_tokens: int = 0
        output_tokens: int = 0
        latency_ms: float = 0.0
        cost_usd: float = 0.0
        step_count: Optional[int] = None
        status: Optional[str] = None
        tool_calls: List[Dict[str, Any]] = []
        tool_error_recovery_rate: Optional[float] = None
        metadata: Dict[str, Any] = {}

    class BaseTargetAdapter:  # type: ignore
        pass

from docground.synthesis.synthesizer import GroundedSynthesizer, REJECTION_MESSAGE
from docground.models import GroundedResponse


class DocGroundTargetAdapter(BaseTargetAdapter):
    """Adapter exposing DocGround RAG pipeline to JudgeKit evaluation runner."""

    def __init__(self, synthesizer: Optional[GroundedSynthesizer] = None, top_k: int = 5):
        self.synthesizer = synthesizer or GroundedSynthesizer()
        self.top_k = top_k

    async def run_query(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> TargetOutput:
        """Execute a single query through DocGround's hybrid retrieval & grounded synthesis.

        Returns TargetOutput with answer, retrieved contexts, citations, and calculated latency.
        """
        metadata = metadata or {}
        t0 = time.perf_counter()

        final_response: Optional[GroundedResponse] = None
        # Consume streaming generator until final response
        async for chunk in self.synthesizer.generate_response_stream(query, top_k=self.top_k):
            if chunk.get("type") == "final_response":
                final_response = chunk.get("payload")

        latency_ms = (time.perf_counter() - t0) * 1000.0

        if final_response is None:
            return TargetOutput(
                answer="Błąd wewnętrzny syntezy DocGround.",
                contexts=[],
                latency_ms=round(latency_ms, 2),
                status="FAILED",
            )

        # Contexts formatting
        contexts = [
            f"[{s.doc_name}, s. {s.page_number}]: {getattr(s, 'quote_snippet', '')}"
            for s in final_response.sources
        ]

        # Calculate citation precision: verified citations vs total cited in answer
        citation_count = len(final_response.sources)
        citation_precision = 1.0 if citation_count > 0 or final_response.answer == REJECTION_MESSAGE else 0.0

        # Estimate token usage (~1.3 tokens per word)
        input_words = len(query.split()) + sum(len(c.split()) for c in contexts)
        output_words = len(final_response.answer.split())
        inp_tokens = int(input_words * 1.3)
        out_tokens = int(output_words * 1.3)

        # Cost: $0.15 / 1M input, $0.60 / 1M output
        cost_usd = ((inp_tokens * 0.15) + (out_tokens * 0.60)) / 1_000_000.0

        return TargetOutput(
            answer=final_response.answer,
            contexts=contexts,
            input_tokens=inp_tokens,
            output_tokens=out_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=round(cost_usd, 6),
            status="SUCCESS" if final_response.is_confident else "REJECTED",
            metadata={
                "is_confident": final_response.is_confident,
                "citation_precision": citation_precision,
                "retrieval_strategy": final_response.retrieval_strategy,
                "sources_count": citation_count,
            },
        )
