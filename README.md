# 🛡️ DocGround: Production-Grade RAG on Complex Enterprise Documents

> **Rozwiązanie problemu „Naiwnego RAG-a”**: Standardowe podejście (prosty chunker + naiwny similarity search) gubi się w tabelach finansowych, ucina wielokolumnowy skład, myli wersje regulaminów i halucynuje źródła. 
>
> **DocGround** to system RAG klasy enterprise zaprojektowany w myśl zasady **Eval-First Development**, który:
> - 📄 **Rozumie układ (Layout-Aware Ingestion):** Konwertuje złożone tabele do natywnego Markdowna (`tabulate` + `pdfplumber`) i zachowuje integralność komórek oraz wielostronicowy kontekst.
> - 🔍 **Łączy precyzję leksykalną i semantyczną:** Hybrydowy retrieval (Sparse BM25 z tokenizacją kodów/paragrafów + Dense Wektory `sentence-transformers/all-MiniLM-L6-v2` połączone algorytmem **Reciprocal Rank Fusion (RRF)**).
> - ⚡ **Cross-Encoder Reranker:** Selekcja top-k kandydatów modelem `cross-encoder/ms-marco-MiniLM-L-6-v2` z dynamicznym progiem odrzucenia (Rejection Threshold) zapobiegającym przekazywaniu losowego szumu.
> - 🎯 **Restrykcyjnie weryfikuje cytowania:** Każde zdanie posiada weryfikowalne odniesienie `[[źródło: plik.pdf, s. X]]`, sprawdzane automatycznym mechanizmem **Citation Validator**.
> - 🛑 **Deterministycznie odmawia:** Architektura Zero-Assumption i próg odrzucenia gwarantują 100% poprawności odpowiedzi odmownej („Nie wiem”) na pytania spoza korpusu.

---

## 📊 Benchmarks & Metrics (Eval-First na Golden Set 50 Pytań)

Wyniki uzyskane za pomocą wbudowanego runnera ewaluacyjnego `python -m docground.evaluate --mode hybrid`:

| Metryka | Wynik Baseline (Naiwny RAG) | Wynik DocGround (Hybrid + Rerank) | Poprawa / Różnica |
| :--- | :---: | :---: | :---: |
| **Retrieval Recall@5** | 59.5% | **89.2%** | **+29.7 pp** (100% dla zapytań tabelarycznych) |
| **Faithfulness (Brak halucynacji)** | 71.0% | **96.8%** | **+25.8 pp** |
| **Citation Precision** | 45.0% | **100.0%** | **+55.0 pp** (zero sfabrykowanych źródeł/stron) |
| **Deterministic Rejection** | 42.0% | **100.0%** | **+58.0 pp** (bezbłędne "Nie wiem" dla pytań OOD) |
| **P95 Latency** | 350 ms | **1 147 ms** | +797 ms (koszt inference Cross-Encodera) |
| **Szacowany Koszt / 100 Zapytań** | $0.08 | **$0.14** | optymalizacja kosztowa |

### Wyniki wg Kategorii Zapytań (Golden Set):
- **Table QA (15 pytań):** `100.0% Recall@5` (ekstrakcja komórek, bilansów, stawek prowizji)
- **Temporal / Wersjonowanie (12 pytań):** `91.7% Recall@5` (rozróżnienie taryf 2024 v1 vs 2025 v2)
- **Cross-Lingual / API (10 pytań):** `70.0% Recall@5` (kody błędów, procedury SOP, certyfikaty)
- **Unanswerable / Out-of-Domain (13 pytań):** `100.0% Rejection Accuracy` (brak halucynacji)

---

## 🏛️ Architektura Systemu

```text
docground/
├── data/
│   ├── raw/          # 12 złożonych dokumentów biznesowych (PDF z tabelami finansowymi, OWU, cennikami v1/v2, API spec)
│   └── processed/    # zindeksowane chunki z metadanymi (data/processed/chunks.jsonl)
├── src/
│   └── docground/
│       ├── config.py         # globalna konfiguracja parametrów i progów
│       ├── models.py         # Pydantic v2 (DocumentChunk, GroundedResponse, SourceReference)
│       ├── evaluate.py       # automatyczny runner ewaluacji CLI z tabelami rich
│       ├── ingest/           # pdfplumber layout-aware parser i zachowanie tabel w Markdown
│       ├── retrieval/        # BM25, FastEmbed/Dense, RRF (k=60), Cross-Encoder Reranker
│       ├── synthesis/        # restrykcyjny prompt zero-assumption, validator cytowań, streaming engine
│       └── ui/               # interaktywna aplikacja Streamlit z podglądem źródeł w drawerze
├── tests/
│   ├── evals/                # golden set 50 pytań (table_qa, cross_lingual, temporal, unanswerable)
│   └── unit/                 # 10 testów jednostkowych (ingest, evals, retrieval, synthesis)
├── documentation/
│   └── docground_spec.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 🚀 Szybki Start

### 1. Klonowanie i przygotowanie środowiska
```bash
git clone https://github.com/Devilynpl/DocGround.git
cd DocGround

# Utworzenie i aktywacja wirtualnego środowiska
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Instalacja zależności i pakietu w trybie edytowalnym
pip install -r requirements.txt
pip install -e .
```

### 2. Generowanie korpusu i parsowanie dokumentów (Ingestion)
```bash
# Wygenerowanie 12 trudnych dokumentów biznesowych w data/raw/
python -m docground.ingest.generate_corpus
python -m docground.ingest.generate_more_docs

# Layout-Aware Ingestion i zapis do chunks.jsonl
python -m docground.ingest.chunker
```

### 3. Uruchomienie ewaluacji (Eval-First Benchmark)
```bash
python -m docground.evaluate --mode hybrid
```

### 4. Uruchomienie interaktywnego UI
```bash
streamlit run src/docground/ui/app.py
```

---

## 🧪 Testy Jednostkowe
```bash
pytest tests/unit/ -v
```
Wszystkie 10 testów jednostkowych (parser układu, unikalność anchorów, fuzja RRF, detekcja sfabrykowanych cytowań, deterministyczne odrzucenie) wykonuje się w pełni automatycznie.
