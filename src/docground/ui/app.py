"""Czysty, minimalistyczny i elegancki Chatbot RAG DocGround (Port 8501).
Skupiony w 100% na konwersacji, weryfikacji faktów i cytowaniach.
Zarządzanie bazą wiedzy i uczenie/ingest przeniesione do osobnego Dashboardu (Port 8502).
"""

import os
import asyncio
import re
from pathlib import Path
import streamlit as st

from docground.config import settings, BASE_DIR
from docground.synthesis.synthesizer import GroundedSynthesizer

st.set_page_config(
    page_title="DocGround Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Elegancki, dopracowany styl czystego chatbota
st.markdown("""
<style>
    /* Ukrycie domyślnego menu i stopki streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Głębokie, eleganckie tło #030408 */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #030408 !important;
        color: #e2e8f0;
    }
    
    [data-testid="stSidebar"] {
        background-color: #060913 !important;
        border-right: 1px solid #141b2d;
    }
    
    .chat-header {
        text-align: center;
        margin-top: -1.5rem;
        margin-bottom: 2rem;
    }
    .chat-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #2563EB, #1D4ED8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }
    .chat-subtitle {
        color: #64748B;
        font-size: 0.95rem;
        margin-top: 0.25rem;
    }
    .badge-verified {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 6px;
    }
    .badge-rejected {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #FEF3C7;
        color: #92400E;
        border: 1px solid #FCD34D;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 6px;
    }
    .source-box {
        background: #F8FAFC;
        border-left: 3px solid #3B82F6;
        padding: 8px 12px;
        margin: 6px 0;
        border-radius: 0 6px 6px 0;
        font-size: 0.85rem;
    }
    .flow-card {
        background: #0d1117;
        color: #c9d1d9;
        font-family: 'Consolas', 'Courier New', monospace;
        padding: 14px;
        border-radius: 8px;
        border-left: 4px solid #58a6ff;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
        font-size: 0.84rem;
        line-height: 1.45;
    }
    .flow-title {
        color: #58a6ff;
        font-weight: 700;
        font-size: 0.92rem;
        margin-bottom: 6px;
    }
    .flow-body {
        white-space: pre-wrap;
        color: #8b949e;
    }
</style>
""", unsafe_allow_html=True)


def get_synthesizer(use_local_llm: bool = True):
    current = st.session_state.get("synthesizer_instance")
    if current is None or getattr(current, "use_local_llm", None) != use_local_llm or not hasattr(current, "_ensure_llm_loaded"):
        st.session_state["synthesizer_instance"] = GroundedSynthesizer(use_local_llm=use_local_llm)
    return st.session_state["synthesizer_instance"]


# Sidebar - silnik syntezy i link do Ingestion Studio
with st.sidebar:
    st.markdown("### ⚙️ Silnik Syntezy")
    
    gemini_key = os.getenv("GEMINI_API_KEY", "") or getattr(settings, "gemini_api_key", "")
    if gemini_key:
        st.success("🟢 **Google Gemini API (Aktywne)**")
        st.caption(f"Model: `{getattr(settings, 'gemini_model_name', 'gemini-2.5-flash')}`")
    else:
        st.info("ℹ️ **Gemini API Key:** nie wykryto w `.env`")
        st.caption("Wklej `GEMINI_API_KEY=...` do pliku `DocGround/.env`")
        
    use_llm = st.toggle("Fallback: Lokalny LLM (Qwen2.5-3B)", value=True, help="Używany gdy brak klucza Gemini lub offline")
    st.markdown("---")
    st.markdown("🎓 **Chcesz dodać nowe dokumenty lub uczyć bazę?**")
    st.markdown("[👉 Otwórz Dashboard Uczenia (Port 8502)](http://localhost:8502)")
    st.markdown("---")
    if st.button("🗑️ Wyczyść historię rozmowy", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

synthesizer = get_synthesizer(use_local_llm=use_llm)

# Dedykowane Logo DocGround AI
logo_path = BASE_DIR / "DocGroundAI_logo.jpg"
if not logo_path.exists():
    logo_path = BASE_DIR.parent / "DocGround" / "DocGroundAI_logo.jpg"

if logo_path.exists():
    col_l1, col_l2, col_l3 = st.columns([1, 2.2, 1])
    with col_l2:
        st.image(str(logo_path), use_container_width=True)
    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="chat-header">
        <div class="chat-title">DocGround AI</div>
        <div class="chat-subtitle">Inteligentny asystent dokumentacji z weryfikacją cytowań i ochroną przed halucynacją</div>
    </div>
    """, unsafe_allow_html=True)

# Podział ekranu na dwie kolumny: Lewa (Konsola Flow) i Prawa (Czat)
col_flow, col_chat = st.columns([1, 1.3], gap="large")

# Inicjalizacja stanu konsoli flow
if "last_flow_steps" not in st.session_state:
    st.session_state.last_flow_steps = [
        {
            "step": "idle",
            "title": "🟢 0. Gotowość Systemu RAG",
            "details": "Oczekiwanie na zapytanie... Konsola w czasie rzeczywistym zwizualizuje etapy:\n1. Query Expansion (PL -> EN)\n2. Hybrydowy Retrieval (BM25 + Dense Vector)\n3. Cross-Encoder Reranking & Threshold Gate\n4. Synteza LLM (Gemini 3.1 Flash-Lite)\n5. Citation & Hallucination Validator"
        }
    ]

with col_flow:
    st.markdown("### 🖥️ Konsola Flow (Pipeline Telemetrii)")
    st.caption("Podgląd na żywo każdego etapu potoku RAG dla ostatniego zapytania:")
    flow_container = st.container()
    
    def render_flow_cards(steps):
        for s in steps:
            st.markdown(f"""
            <div class="flow-card">
                <div class="flow-title">{s.get('title', '')}</div>
                <div class="flow-body">{s.get('details', '')}</div>
            </div>
            """, unsafe_allow_html=True)

    with flow_container:
        render_flow_cards(st.session_state.last_flow_steps)

with col_chat:
    st.markdown("### 💬 Interaktywny Czat z Dokumentacją")
    # Inicjalizacja historii wiadomości
    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_history_container = st.container()
    with chat_history_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "meta" in msg and msg["meta"]:
                    meta = msg["meta"]
                    if meta.get("is_confident"):
                        st.markdown('<div class="badge-verified">✓ Zweryfikowano w dokumentach źródłowych</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="badge-rejected">⚠️ Brak potwierdzenia w bazie wiedzy (Odmowa)</div>', unsafe_allow_html=True)
                    
                    if meta.get("sources"):
                        with st.expander(f"📚 Zobacz źródła ({len(meta['sources'])})", expanded=False):
                            for s in meta["sources"]:
                                st.markdown(f"**📄 {s['doc_name']}** (str. {s['page_number']})")
                                st.code(s['quote_snippet'], language="text")

    # Chat input
    if prompt := st.chat_input("Zadaj pytanie dotyczące dokumentów..."):
        # Zapisz wiadomość użytkownika
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_history_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            # Odpowiedź asystenta ze strumieniowaniem
            with st.chat_message("assistant"):
                response_box = st.empty()
                current_flow = []
                flow_placeholder = flow_container.empty()
                
                async def stream_response():
                    collected_text = ""
                    final_payload = None
                    stream = synthesizer.generate_response_stream(prompt, top_k=5)
                    async for chunk in stream:
                        if chunk["type"] == "flow_step":
                            current_flow.append(chunk)
                            cards_html = "".join([
                                f'<div class="flow-card"><div class="flow-title">{s.get("title", "")}</div><div class="flow-body">{s.get("details", "")}</div></div>'
                                for s in current_flow
                            ])
                            flow_placeholder.markdown(cards_html, unsafe_allow_html=True)
                        elif chunk["type"] == "token":
                            collected_text += chunk["content"]
                            response_box.markdown(collected_text + "▌")
                        elif chunk["type"] == "final_response":
                            final_payload = chunk["payload"]
                    return collected_text, final_payload
                
                full_reply, payload = asyncio.run(stream_response())
                st.session_state.last_flow_steps = current_flow

                # Oczyszczenie tekstu z technicznych znaczników [[źródło: ...]]
                clean_reply = re.sub(r"\[\[(?:źródło|source):.*?\]\]", "", full_reply, flags=re.IGNORECASE).strip()
                clean_reply = re.sub(r"\s{2,}", " ", clean_reply)
                response_box.markdown(clean_reply)

                meta = None
                if payload:
                    if payload.is_confident:
                        st.markdown('<div class="badge-verified">✓ Zweryfikowano w dokumentach źródłowych</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="badge-rejected">⚠️ Brak potwierdzenia w bazie wiedzy (Odmowa)</div>', unsafe_allow_html=True)

                    if payload.sources:
                        with st.expander(f"📚 Zobacz źródła ({len(payload.sources)})", expanded=False):
                            for s in payload.sources:
                                st.markdown(f"**📄 {s.doc_name}** (str. {s.page_number})")
                                st.code(s.quote_snippet, language="text")

                    meta = {
                        "is_confident": payload.is_confident,
                        "sources": [s.model_dump() for s in payload.sources]
                    }

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": clean_reply,
                    "meta": meta
                })
