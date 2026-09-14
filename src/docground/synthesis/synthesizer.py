"""Synthesizer Engine:
Wspiera asynchroniczną syntezę ze streamingiem tokenów, deterministyczną odmową na progu odrzucenia
oraz automatyczną weryfikacją cytowań przed zwróceniem GroundedResponse.
"""

import asyncio
import re
from typing import AsyncGenerator, List, Tuple, Optional, Dict, Any
from docground.models import GroundedResponse, SourceReference, DocumentChunk
from docground.synthesis.prompts import STRICT_SYSTEM_PROMPT, format_context_prompt
from docground.synthesis.citation_validator import CitationValidator
from docground.retrieval.engine import HybridSearchEngine


import os
from pathlib import Path
from docground.config import BASE_DIR, settings

REJECTION_MESSAGE = "Na podstawie dostarczonej dokumentacji nie jestem w stanie odpowiedzieć na to pytanie."

# Check for local GGUF model: BASE_DIR to DocGround, więc BASE_DIR.parent to Ai_Engineer_Portfolio
LOCAL_MODEL_PATH = BASE_DIR.parent / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"
print(f"[GroundedSynthesizer] LOCAL_MODEL_PATH: {LOCAL_MODEL_PATH} (exists: {LOCAL_MODEL_PATH.exists()})")


class GroundedSynthesizer:
    def __init__(
        self,
        search_engine: Optional[HybridSearchEngine] = None,
        use_local_llm: bool = False,
        model_path: Optional[Path] = None,
    ):
        self.search_engine = search_engine or HybridSearchEngine()
        self.validator = CitationValidator()
        self.use_local_llm = use_local_llm
        self.llm = None

        self.model_path = model_path or LOCAL_MODEL_PATH
        if self.use_local_llm:
            self._ensure_llm_loaded()

    def _ensure_llm_loaded(self):
        if self.llm is None and self.model_path.exists():
            try:
                from llama_cpp import Llama
                print(f"[GroundedSynthesizer] Ładowanie lokalnego modelu LLM: {self.model_path.name}...")
                self.llm = Llama(
                    model_path=str(self.model_path),
                    n_ctx=8192,
                    n_threads=os.cpu_count() or 4,
                    verbose=False,
                )
                print("[GroundedSynthesizer] Lokalny model LLM załadowany pomyślnie.")
            except Exception as e:
                print(f"[GroundedSynthesizer] Ostrzeżenie: nie udało się zainicjalizować Llama: {e}")
                self.llm = None

    async def generate_response_stream(
        self,
        query: str,
        top_k: int = 5
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Asynchroniczny generator strumieniowy zwracający tokeny w czasie rzeczywistym,
        a na końcu ustrukturyzowany obiekt GroundedResponse.
        """
        # 0. Rozwinięcie zapytania (Query Expansion)
        from docground.retrieval.query_expander import expand_query
        expanded_q = expand_query(query)
        yield {
            "type": "flow_step",
            "step": "query_expansion",
            "title": "🔍 1. Rozwinięcie zapytania (Query Expansion)",
            "details": f"Oryginał: {query}\nRozwinięte: {expanded_q}"
        }

        # 1. Sparse BM25 + Dense Vector
        bm25_hits = self.search_engine.bm25.search(expanded_q, top_k=settings.bm25_top_k)
        dense_hits = self.search_engine.dense.search(expanded_q, top_k=settings.dense_top_k)
        
        bm25_summary = ", ".join([f"{c.doc_name} p.{c.page_number} ({s:.2f})" for c, s in bm25_hits[:3]])
        dense_summary = ", ".join([f"{c.doc_name} p.{c.page_number} ({s:.2f})" for c, s in dense_hits[:3]])
        yield {
            "type": "flow_step",
            "step": "retrieval",
            "title": "⚡ 2. Hybrydowy Retrieval (BM25 + Dense)",
            "details": f"BM25 (Sparse) Top 3: {bm25_summary or 'Brak'}\nDense Vector Top 3: {dense_summary or 'Brak'}"
        }

        # 2. Reciprocal Rank Fusion & Reranking
        from docground.retrieval.rrf import reciprocal_rank_fusion
        rrf_res = reciprocal_rank_fusion(dense_hits, bm25_hits, k=settings.rrf_k, top_k=15)
        candidates = [c for c, _ in rrf_res]
        
        reranked_res, is_low_confidence = self.search_engine.reranker.rerank(
            query=expanded_q,
            candidates=candidates,
            top_k=top_k,
            threshold=settings.rejection_threshold
        )
        results = reranked_res
        retrieved_chunks = [ch for ch, _ in results]

        rerank_summary = "\n".join([f"  • {c.doc_name} (str. {c.page_number}) -> Score: {s:.4f}" for c, s in results])
        yield {
            "type": "flow_step",
            "step": "reranking",
            "title": f"🎯 3. Cross-Encoder Reranking (mmarco-mMiniLMv2)",
            "details": f"Próg odrzucenia: {settings.rejection_threshold}\nLow Confidence: {is_low_confidence}\nWyselekcjonowane fragmenty:\n{rerank_summary}"
        }

        # 3. Synteza: Gemini Flash API (priorytet, gdy podany klucz), Local Qwen LLM lub deterministyczny offline engine
        answer_raw = ""
        last_error = ""
        gemini_key = getattr(settings, "gemini_api_key", "") or os.getenv("GEMINI_API_KEY", "")
        active_engine = "Gemini 3.1 Flash-Lite" if gemini_key else ("Local Qwen2.5-3B" if self.use_local_llm else "No LLM Configured")

        yield {
            "type": "flow_step",
            "step": "synthesis_start",
            "title": f"🧠 4. Generowanie Odpowiedzi ({active_engine})",
            "details": f"Liczba przekazanych chunków: {len(retrieved_chunks)}\nModel: {active_engine}"
        }

        # 3. Synteza przez Tollgate LLM Gateway (Port 8000) z obsługą cache, budżetów i retry
        user_prompt = format_context_prompt(query, results)
        tollgate_url = os.getenv("TOLLGATE_URL", "http://127.0.0.1:8000/v1/chat")
        
        if retrieved_chunks:
            try:
                import urllib.request
                import json
                
                payload_gate = {
                    "app": "docground",
                    "messages": [
                        {"role": "system", "content": STRICT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "metadata": {"corpus_version": "v1"}
                }
                req_gate = urllib.request.Request(
                    tollgate_url,
                    data=json.dumps(payload_gate).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        # SECURITY FIX (CRITICAL-02): Internal auth header required by TollGate middleware.
                        "X-Tollgate-Key": os.getenv("TOLLGATE_INTERNAL_KEY", ""),
                    }
                )
                loop = asyncio.get_running_loop()
                def call_gate():
                    with urllib.request.urlopen(req_gate, timeout=25) as resp:
                        return json.loads(resp.read().decode("utf-8"))

                gate_data = await loop.run_in_executor(None, call_gate)
                if not gate_data.get("error"):
                    answer_raw = gate_data.get("text", "").strip()
                    is_cached = gate_data.get("cached", False)
                    print(f"[Synthesizer] Odpowiedź z Tollgate (cached={is_cached}, route={gate_data.get('route')}, latency={gate_data.get('latency_ms')}ms)")
                else:
                    print(f"[Synthesizer] Ostrzeżenie Tollgate: {gate_data.get('error')}")
            except Exception as eg:
                print(f"[GroundedSynthesizer] Tollgate Gateway offline ({eg}), sprawdzam bezpośredni dostęp...")

        # Bezpośredni fallback do Gemini gdyby Tollgate nie odpowiadał
        if not answer_raw and gemini_key and retrieved_chunks:
            try:
                import urllib.request
                import json
                model_name = getattr(settings, "gemini_model_name", "gemini-3.1-flash-lite")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                
                payload = {
                    "contents": [{
                        "parts": [{"text": f"{STRICT_SYSTEM_PROMPT}\n\n{user_prompt}"}]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 600
                    }
                }
                
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                
                loop = asyncio.get_running_loop()
                def call_gemini():
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        return json.loads(resp.read().decode("utf-8"))

                data = await loop.run_in_executor(None, call_gemini)
                answer_raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                print(f"[Synthesizer] Bezpośredni Gemini answer raw: {answer_raw}")
            except Exception as e:
                last_error = f"Błąd Gemini API: {e}"
                print(f"[GroundedSynthesizer] {last_error}, próba AWS Bedrock / lokalnego LLM.")

        # Bezpośredni fallback do AWS Bedrock (Anthropic Claude 3.5 / 4.5 Sonnet)
        if not answer_raw and retrieved_chunks:
            aws_key = os.getenv("AWS_ACCESS_KEY_ID", "")
            aws_sec = os.getenv("AWS_SECRET_ACCESS_KEY", "")
            aws_model = os.getenv(
                "AWS_BEDROCK_MODEL_ID",
                "arn:aws:bedrock:eu-central-1:832191487769:inference-profile/eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
            )
            if aws_key and aws_sec and aws_model:
                try:
                    import boto3
                    boto_client = boto3.Session(
                        aws_access_key_id=aws_key,
                        aws_secret_access_key=aws_sec,
                        region_name=os.getenv("AWS_REGION", "eu-central-1")
                    ).client("bedrock-runtime")
                    loop = asyncio.get_running_loop()

                    def call_bedrock():
                        resp = boto_client.converse(
                            modelId=aws_model,
                            system=[{"text": STRICT_SYSTEM_PROMPT}],
                            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                            inferenceConfig={"maxTokens": 1024, "temperature": 0.1}
                        )
                        output_msg = resp.get("output", {}).get("message", {})
                        txt = ""
                        for c in output_msg.get("content", []):
                            if "text" in c:
                                txt += c["text"]
                        return txt

                    answer_raw = await loop.run_in_executor(None, call_bedrock)
                    print(f"[Synthesizer] AWS Bedrock Claude answer raw: {answer_raw[:80]}...")
                except Exception as eb:
                    last_error = f"Błąd AWS Bedrock API: {eb}"
                    print(f"[GroundedSynthesizer] {last_error}")

        if not answer_raw and self.use_local_llm and self.llm and retrieved_chunks:
            try:
                user_prompt = format_context_prompt(query, results)
                loop = asyncio.get_running_loop()
                
                def run_llm():
                    return self.llm.create_chat_completion(
                        messages=[
                            {"role": "system", "content": STRICT_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.1,
                        max_tokens=256,
                    )

                completion = await loop.run_in_executor(None, run_llm)
                answer_raw = completion["choices"][0]["message"]["content"].strip()
                print(f"[Synthesizer] Local LLM answer raw: {answer_raw}")
            except Exception as e:
                last_error = f"Błąd inferencji lokalnego LLM: {e}"
                print(f"[GroundedSynthesizer] {last_error}")
                answer_raw = f"BŁĄD MODELU: {last_error}"
        if not answer_raw:
            if last_error:
                answer_raw = f"BŁĄD MODELU: {last_error}"
            else:
                answer_raw = "BŁĄD MODELU: Brak skonfigurowanego klucza API (Gemini/AWS) i brak lokalnego LLM."

        # 3. Post-Processing Citation Validator
        is_all_valid, verified_sources, sanitized_answer = self.validator.validate_citations(
            answer_raw, retrieved_chunks
        )

        is_confident = (sanitized_answer != REJECTION_MESSAGE) and is_all_valid

        yield {
            "type": "flow_step",
            "step": "validation",
            "title": "🛡️ 5. Post-Processing Citation Validator",
            "details": f"Status: {'✓ Zweryfikowano' if is_confident else '⚠️ Odrzucono (Brak ugruntowania)'}\nLiczba potwierdzonych źródeł: {len(verified_sources)}"
        }

        # 4. Strumieniowanie tokenów (słów)
        words = sanitized_answer.split()
        for i, word in enumerate(words):
            yield {"type": "token", "content": word + (" " if i < len(words) - 1 else "")}
            await asyncio.sleep(0.015)

        # 5. Zwrócenie ustrukturyzowanego kontraktu na końcu strumienia
        if "gate_data" in locals() and "bedrock" in str(gate_data.get("route", "")):
            strategy_name = "Hybrid BM25 + Dense + RRF + CrossEncoder + AWS Bedrock Claude Sonnet (Tollgate Failover)"
        elif gemini_key and answer_raw and "bedrock" not in str(locals().get("aws_model", "")).lower():
            strategy_name = f"Hybrid BM25 + Dense + RRF + CrossEncoder + Google Gemini ({settings.gemini_model_name})"
        elif answer_raw and "boto_client" in locals():
            strategy_name = "Hybrid BM25 + Dense + RRF + CrossEncoder + AWS Bedrock Claude 3.5/4.5 Sonnet"
        elif self.use_local_llm and self.llm:
            strategy_name = "Hybrid BM25 + Dense + RRF + CrossEncoder + Qwen2.5-3B Local LLM"
        else:
            strategy_name = "Hybrid BM25 + Dense + RRF + CrossEncoder (No LLM)"
        grounded_resp = GroundedResponse(
            answer=sanitized_answer,
            is_confident=is_confident,
            sources=verified_sources,
            retrieval_strategy=strategy_name
        )
        yield {"type": "final_response", "payload": grounded_resp}
