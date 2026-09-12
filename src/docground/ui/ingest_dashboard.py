"""Dedykowany Dashboard Ingestion & Zarządzania Bazą Wiedzy (DocGround Ingestion Studio):
- Drag & Drop Upload PDF z podglądem i konfiguracją parametrów chunkingu
- Batch Ingestion z katalogu DocGround/data/raw/ z paskiem postępu w czasie rzeczywistym
- Inspekcja struktury dokumentów, bloków layoutu i wyekstrahowanych tabel Markdown
- Podgląd statystyk bazy wektorowej i indeksu BM25
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st

# Setup sys.path
ROOT = Path(__file__).resolve().parent.parent.parent.parent
DOCGROUND_SRC = ROOT / "DocGround" / "src"
if str(DOCGROUND_SRC) not in sys.path:
    sys.path.insert(0, str(DOCGROUND_SRC))

from docground.config import RAW_DATA_DIR, CHUNKS_PATH, settings, BASE_DIR
from docground.ingest.parser import LayoutAwareParser
from docground.ingest.chunker import SemanticTablePreservingChunker
from docground.models import DocumentChunk

st.set_page_config(
    page_title="DocGround | Ingestion Studio & Knowledge Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #030408 !important;
        color: #e2e8f0;
    }
    [data-testid="stSidebar"] {
        background-color: #060913 !important;
        border-right: 1px solid #141b2d;
    }
    .studio-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 0.2rem;
    }
    .studio-sub {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
    }
    .card-metric {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .card-metric h2 {
        color: #38BDF8;
        font-size: 2.2rem;
        margin: 0;
    }
    .card-metric p {
        color: #94A3B8;
        font-size: 0.95rem;
        margin: 4px 0 0 0;
    }
</style>
""", unsafe_allow_html=True)


def get_knowledge_base_details():
    chunks: List[Dict[str, Any]] = []
    doc_groups: Dict[str, List[Dict[str, Any]]] = {}
    table_count = 0
    text_count = 0

    if CHUNKS_PATH.exists():
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        c = json.loads(line)
                        chunks.append(c)
                        d_name = c.get("doc_name", "unknown")
                        if d_name not in doc_groups:
                            doc_groups[d_name] = []
                        doc_groups[d_name].append(c)
                        if c.get("chunk_type") == "table":
                            table_count += 1
                        else:
                            text_count += 1
                    except Exception:
                        pass

    return {
        "total_chunks": len(chunks),
        "doc_groups": doc_groups,
        "unique_docs_count": len(doc_groups),
        "table_count": table_count,
        "text_count": text_count,
    }


kb_info = get_knowledge_base_details()

# Sidebar: Parametry silnika parsowania
with st.sidebar:
    st.image("https://img.shields.io/badge/Pipeline-Layout--Aware%20Ingestion-emerald?style=for-the-badge", use_container_width=True)
    st.markdown("### ⚙️ Parametry Chunkingu")
    chunk_size = st.number_input("Docelowy rozmiar chunka (tokeny)", min_value=100, max_value=1500, value=settings.chunk_size, step=50)
    chunk_overlap = st.number_input("Overlap chunków (tokeny)", min_value=10, max_value=300, value=settings.chunk_overlap, step=10)
    preserve_tables = st.checkbox("Zachowaj tabele jako atomowe chunki", value=True, help="Zapobiega rozcinaniu tabel na granicy chunków (Table Preservation).")

    st.markdown("---")
    st.markdown("### 📁 Szybkie Akcje")
    if st.button("🧹 Wyczyść indeks bazy wiedzy", type="secondary", use_container_width=True):
        if CHUNKS_PATH.exists():
            CHUNKS_PATH.unlink()
            st.toast("Wyczyszczono plik chunks.jsonl!", icon="🗑️")
            time.sleep(0.5)
            st.rerun()

# Dedykowane Logo DocGround AI
logo_path = BASE_DIR / "DocGroundAI_logo.jpg"
if not logo_path.exists():
    logo_path = BASE_DIR.parent / "DocGround" / "DocGroundAI_logo.jpg"

if logo_path.exists():
    col_l1, col_l2, col_l3 = st.columns([1, 2.2, 1])
    with col_l2:
        st.image(str(logo_path), use_container_width=True)
    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

st.markdown('<div class="studio-header">⚡ DocGround: Ingestion Studio & Knowledge Hub</div>', unsafe_allow_html=True)
st.markdown('<div class="studio-sub">Dedykowany panel importu dokumentów, ekstrakcji tabel i zasilania bazy wiedzy RAG</div>', unsafe_allow_html=True)

# Górne karty metryk
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(f'<div class="card-metric"><h2>{kb_info["unique_docs_count"]}</h2><p>Zindeksowane Dokumenty</p></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="card-metric"><h2>{kb_info["total_chunks"]}</h2><p>Aktywne Chunki</p></div>', unsafe_allow_html=True)
with col_m3:
    st.markdown(f'<div class="card-metric"><h2>{kb_info["table_count"]}</h2><p>Wyekstrahowane Tabele</p></div>', unsafe_allow_html=True)
with col_m4:
    raw_files_count = len(list(RAW_DATA_DIR.glob("*.pdf")))
    st.markdown(f'<div class="card-metric"><h2>{raw_files_count}</h2><p>Pliki w data/raw</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

nav_tab1, nav_tab2, nav_tab3 = st.tabs([
    "📥 Import Pojedynczego PDF (Upload)",
    "📦 Masowy Batch Ingest (z data/raw)",
    "📑 Eksplorator Zindeksowanych Danych"
])

# -------------------------------------------------------------
# TAB 1: Pojedynczy upload
# -------------------------------------------------------------
with nav_tab1:
    st.markdown("#### 📤 Wgraj i przetwórz dokument PDF")
    st.caption("Dokument zostanie poddany analizie układu, ekstrakcji tabel do formatu Markdown i dołączony do bazy wiedzy.")

    uploaded_pdf = st.file_uploader("Wybierz plik PDF z dysku:", type=["pdf"])
    max_pages_limit = st.slider("Maksymalna liczba stron do przeanalizowania:", min_value=1, max_value=50, value=10)

    if uploaded_pdf is not None:
        st.write(f"Plik: `{uploaded_pdf.name}` (Rozmiar: {uploaded_pdf.size / 1024:.1f} KB)")
        if st.button("🚀 Rozpocznij Ingestion i Zindeksuj", type="primary"):
            progress = st.progress(10)
            status = st.empty()

            status.info(f"Zapisywanie pliku do `{RAW_DATA_DIR.name}/`...")
            dest_file = RAW_DATA_DIR / uploaded_pdf.name
            with open(dest_file, "wb") as f:
                f.write(uploaded_pdf.getbuffer())
            progress.progress(30)

            status.info("Ekstrakcja bloków tekstu i tabel layout-aware parserem...")
            parser = LayoutAwareParser()
            blocks = parser.parse_pdf(dest_file, max_pages=max_pages_limit)
            progress.progress(60)

            status.info("Dzielenie na semantyczne chunki...")
            chunker = SemanticTablePreservingChunker(
                max_tokens=chunk_size,
                overlap_tokens=chunk_overlap,
            )
            chunks = chunker.chunk_blocks(blocks)
            progress.progress(85)

            status.info("Zapisywanie do bazy wektorowej i słownikowej...")
            with open(CHUNKS_PATH, "a", encoding="utf-8") as f:
                for ch in chunks:
                    f.write(ch.model_dump_json() + "\n")
            progress.progress(100)

            st.success(f"🎉 Sukces! Dodano {len(chunks)} nowych chunków z dokumentu `{uploaded_pdf.name}` do bazy wiedzy.")
            time.sleep(1)
            st.rerun()

# -------------------------------------------------------------
# TAB 2: Batch Ingestion z data/raw
# -------------------------------------------------------------
with nav_tab2:
    st.markdown("#### 📦 Masowe zasilanie bazy wiedzy z katalogu `data/raw/`")
    raw_pdfs = sorted(list(RAW_DATA_DIR.glob("*.pdf")))
    already_indexed_docs = set(kb_info["doc_groups"].keys())

    unindexed_pdfs = [p for p in raw_pdfs if p.name not in already_indexed_docs]
    st.write(f"- Wszystkie pliki PDF w katalogu: **{len(raw_pdfs)}**")
    st.write(f"- Pliki już zindeksowane: **{len(already_indexed_docs)}**")
    st.write(f"- Pliki oczekujące na indeksowanie: **{len(unindexed_pdfs)}**")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        batch_size = st.slider("Ile kolejnych plików przetworzyć w tej partii:", min_value=1, max_value=min(50, len(unindexed_pdfs) or 1), value=min(10, len(unindexed_pdfs) or 1))
    with col_b2:
        pages_per_doc = st.slider("Liczba stron na dokument:", min_value=1, max_value=20, value=5)

    if st.button("⚡ Uruchom Batch Ingestion", type="primary", disabled=(len(unindexed_pdfs) == 0)):
        p_bar = st.progress(0)
        p_status = st.empty()

        parser = LayoutAwareParser()
        chunker = SemanticTablePreservingChunker(
            max_tokens=chunk_size,
            overlap_tokens=chunk_overlap,
        )

        batch_targets = unindexed_pdfs[:batch_size]
        newly_created_chunks = []

        for idx, pdf_file in enumerate(batch_targets):
            p_status.markdown(f"**Przetwarzanie [{idx+1}/{len(batch_targets)}]:** `{pdf_file.name}`...")
            try:
                blocks = parser.parse_pdf(pdf_file, max_pages=pages_per_doc)
                file_chunks = chunker.chunk_blocks(blocks)
                newly_created_chunks.extend(file_chunks)
            except Exception as ex:
                st.error(f"Błąd przy pliku {pdf_file.name}: {ex}")
            p_bar.progress((idx + 1) / len(batch_targets))

        if newly_created_chunks:
            with open(CHUNKS_PATH, "a", encoding="utf-8") as f:
                for ch in newly_created_chunks:
                    f.write(ch.model_dump_json() + "\n")

        st.success(f"🎉 Batch ingest zakończony pomyślnie! Zindeksowano {len(batch_targets)} dokumentów i dodano {len(newly_created_chunks)} chunków.")
        time.sleep(1)
        st.rerun()

# -------------------------------------------------------------
# TAB 3: Eksplorator Bazy Wiedzy
# -------------------------------------------------------------
with nav_tab3:
    st.markdown("#### 📑 Przegląd zawartości bazy wiedzy")
    if not kb_info["doc_groups"]:
        st.info("Baza wiedzy jest pusta. Wgraj plik w pierwszej zakładce.")
    else:
        doc_list = sorted(list(kb_info["doc_groups"].keys()))
        selected_file = st.selectbox("Wybierz zindeksowany dokument do inspekcji:", doc_list)

        chunks_for_file = kb_info["doc_groups"].get(selected_file, [])
        st.markdown(f"Dokument: **`{selected_file}`** | Liczba chunków: **{len(chunks_for_file)}**")

        for idx, ch in enumerate(chunks_for_file, start=1):
            chunk_type_badge = "📊 Tabela" if ch.get("chunk_type") == "table" else "📝 Tekst"
            with st.expander(f"Chunk #{idx} | Strona {ch.get('page_number')} | {chunk_type_badge}", expanded=False):
                st.markdown(f"**Chunk ID:** `{ch.get('chunk_id')}`")
                st.markdown(f"**Raw Anchor:** `{ch.get('raw_context_anchor', '')}`")
                st.markdown("---")
                if ch.get("chunk_type") == "table":
                    st.markdown("##### Wyrenderowana tabela Markdown:")
                    st.markdown(ch.get("content"))
                else:
                    st.text(ch.get("content"))
