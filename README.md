# 🛡️ DocGround: Production-Grade RAG on Complex Enterprise Documents

> **Rozwiązanie problemu „Naiwnego RAG-a”**: Standardowe podejście (prosty chunker + naiwny similarity search) gubi się w tabelach finansowych, ucina wielokolumnowy skład, myli wersje regulaminów i halucynuje źródła. 
>
> **DocGround** to system RAG klasy enterprise zaprojektowany w myśl zasady **Eval-First Development**, który:
> - 📄 **Rozumie układ (Layout-Aware Ingestion):** Konwertuje złożone tabele do natywnego Markdowna i zachowuje granice sekcji wielostronicowych dokumentów.
> - 🔍 **Łączy precyzję leksykalną i semantyczną:** Hybrydowy retrieval (Sparse BM25 + Dense Vectors z Reciprocal Rank Fusion) doprawiony dwuetapowym Cross-Encoder Rerankerem.
> - 🎯 **Restrykcyjnie weryfikuje cytowania:** Każde zdanie posiada weryfikowalne odniesienie `[[źródło: plik, s. strona]]`, sprawdzane mechanizmem post-processing validatora.
> - 🛑 **Deterministycznie odmawia:** Posiada próg odrzucenia (Rejection Threshold) i mechanizm Zero-Assumption („Nie wiem” zamiast halucynacji).

---

## 📊 Benchmarks & Metrics (Eval-First)

| Metryka | Wynik Baseline (Naiwny RAG) | Wynik DocGround (Hybrid + Rerank) |
| :--- | :---: | :---: |
| **Retrieval Recall@5** | TBD (Phase 2/5) | TBD (Phase 2/5) |
| **Faithfulness (Brak halucynacji)** | TBD (Phase 2/5) | TBD (Phase 2/5) |
| **Citation Precision** | TBD (Phase 2/5) | TBD (Phase 2/5) |
| **P95 Latency** | TBD | TBD |
| **Koszt / 100 zapytań** | TBD | TBD |

---

## 🏛️ Architektura Systemu

```text
docground/
├── data/
│   ├── raw/          # dokumenty wejściowe (PDF/HTML z tabelami, regulaminy)
│   └── processed/    # zindeksowane chunki z metadanymi (chunks.jsonl)
├── src/
│   └── docground/
│       ├── ingest/   # parsowanie układu, tabele, chunking
│       ├── retrieval/# wektory, BM25, RRF, reranker
│       ├── synthesis/# prompt kompilacji, weryfikator cytowań
│       └── ui/       # interfejs streamingowy (Streamlit)
├── tests/
│   ├── evals/        # golden set (50 pytań) i skrypt metryk
│   └── unit/         # testy jednostkowe
├── documentation/
│   └── docground_spec.md
├── pyproject.toml
├── requirements.txt
└── README.md
```
