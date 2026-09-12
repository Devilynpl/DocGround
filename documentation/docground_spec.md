# DocGround: Produkcyjny RAG na Trudnym Korpusie z Weryfikowalnymi Cytowaniami

**Problem:** Standardowy pipeline „naiwnego RAG-a” (prosty chunker + similarity search) kompletnie zawodzi na realnych dokumentach: ucina tabele w połowie, gubi metadane stron, myli wersje regulaminów i zmyśla cytowania.  
**Cel:** Zbudować odporny system RAG, który odpowiada wyłącznie na podstawie faktów, podaje dokładne cytaty (plik, strona, fragment), a przy braku pewności zwraca deterministyczne „nie wiem”.  
**Zasada przewodnia:** Eval-First Development — metryki i zbiór testowy powstają przed napisaniem jakiegokolwiek interfejsu graficznego.

---

## ~~Faza 1: Selekcja korpusu, taksonomia chunkingu i schemat metadanych~~
~~Zanim model dostanie jakikolwiek tekst, musisz rozwiązać problem reprezentacji danych. Zwykły podział po 500 znakach niszczy semantykę tabel i strukturę dokumentu wielostronicowego.~~

- [x] ~~**Wybór trudnego korpusu biznesowego (min. 10–20 złożonych plików):**~~
  - ~~Odrzucenie czystego tekstu (np. artykułów z Wikipedii).~~
  - ~~Wybór dokumentów zawierających: tabele finansowe, wielokolumnowy skład tekstu, regulaminy z numerowanymi sekcjami (np. OWU, instrukcje techniczne, dokumentacja API w HTML/PDF).~~ *(Zrealizowano 12 trudnych plików PDF w `data/raw/`)*
- [x] ~~**Zaawansowany parser dokumentów (Layout-Aware Ingestion):**~~
  - ~~Integracja parsera strukturalnego (pdfplumber) zdolnego do rozpoznawania nagłówków, akapitów i bloków tabelarycznych.~~
  - ~~Ekstrakcja tabel do natywnego formatu Markdown lub HTML — modele znacznie lepiej rozumieją relacje wiersz-kolumna w sformatowanym tekście niż w płaskim ciągu tokenów.~~ *(Zrealizowano w `docground.ingest.parser`)*
- [x] ~~**Hierarchiczny kontrakt metadanych per chunk:**~~
  - ~~Każdy fragment tekstu musi być trwale związany z metadanymi:~~
```python
class DocumentChunk(BaseModel):
    chunk_id: str             # unikalny hash (np. sha256 z treści i źródła)
    doc_name: str             # np. regulamin_promocji_v2.pdf
    doc_type: str             # pdf, html, sop
    page_number: int          # numer strony fizycznej (lub sekcja HTML)
    chunk_type: str           # text, table, header
    content: str              # faktyczny tekst chunka
    raw_context_anchor: str   # unikalne pierwsze i ostatnie 10 słów do weryfikacji cytatu
```
*(Zrealizowano w `docground.models` z Pydantic v2)*
- [x] ~~**Strategia chunkingu semantycznego (Recursive + Table Preservation):**~~
  - ~~Nigdy nie dziel komórek tabeli w połowie. Cała tabela stanowi pojedynczy chunk lub podtabelę z zachowanym nagłówkiem kolumn.~~
  - ~~Chunk size: 400–600 tokenów z nakładaniem (overlap) 80–100 tokenów.~~ *(Zrealizowano w `docground.ingest.chunker`)*

---

## ~~Faza 2: Eval-First — Budowa Golden Setu i metryk przed RAG-iem~~
~~Nie budujemy retrievalu „na oko”. W tej fazie tworzysz fundament testowy, który będzie obiektywnym sędzią dla każdej zmiany algorytmu.~~

- [x] ~~**Przygotowanie specyficznego Golden Setu (40–60 pytań):**~~
  - ~~Pytania tabelaryczne (Table QA): Pytania o konkretne komórki (15 pytań).~~
  - ~~Pytania wielojęzyczne / krzyżowe: Pytania po polsku do dokumentacji angielskiej (10 pytań).~~
  - ~~Pytania sprzeczne temporalnie: Porównanie wersji v1 vs v2 (12 pytań).~~
  - ~~Pytania spoza korpusu (Unanswerable / Out-of-Domain): Min. 20% pytań (13 pytań = 26% zbioru, test deterministycznego „nie wiem”).~~ *(Zrealizowano 50 pytań w `tests/evals/golden_set.json`)*
- [x] ~~**Definicja 5 kluczowych metryk (metryki sukcesu w README):**~~
  - ~~Recall@K (Retrieval Recall): Czy właściwy chunk z odpowiedzią znalazł się w top K pobranych dokumentów.~~
  - ~~Faithfulness (Wierność): Brak halucynacji — czy każda informacja wynika bezpośrednio z pobranego kontekstu.~~
  - ~~Citation Precision (Precyzja cytowań): Odsetek cytowań, które rzeczywiście wskazują właściwy plik, stronę i dokładnie wspierają dane zdanie.~~
  - ~~P95 Latency: Czas generacji odpowiedzi dla 95% najtrudniejszych zapytań.~~
  - ~~Cost per 100 Queries: Całkowity koszt tokenów (embedder + LLM + reranker) na 100 wywołań.~~ *(Zrealizowano w `docground.evals.metrics`)*
- [x] ~~**Zautomatyzowany runner walidacji (CLI):**~~
  - ~~Prosty skrypt `python -m docground.evaluate`, który uruchamia zbiór testowy i zwraca wyniki w tabeli terminala.~~ *(Zrealizowano w `docground.evaluate` z formatowaniem `rich`)*

---

## ~~Faza 3: Silnik wyszukiwania hybrydowego (BM25 + Dense Vectors + Cross-Encoder Reranker)~~
~~Pojedynczy wektorowy retriever zawodzi przy nazwach własnych, numerach artykułów, kodach błędów i skrótach. Rozwiązaniem jest wyszukiwanie hybrydowe z późniejszym rerankingiem.~~

- [x] ~~**Baza wektorowa i model embeddingów (Dense Retrieval):**~~
  - ~~Zastosowanie sprawdzonego modelu wielojęzycznego (FastEmbed all-MiniLM-L6-v2 ONNX).~~
  - ~~Przechowywanie wektorów z normalizacją L2 i filtrowaniem po metadanych.~~ *(Zrealizowano w `docground.retrieval.dense`)*
- [x] ~~**Wyszukiwanie leksykalne (Sparse Retrieval / BM25):**~~
  - ~~Wdrożenie indeksu BM25 z tokenizacją kodów błędów, artykułów prawnych i liczb.~~
  - ~~Kluczowe dla zapytań precyzyjnych (np. „Art. 14 ust. 2b”, „błąd ERR_0x8004”).~~ *(Zrealizowano w `docground.retrieval.bm25`)*
- [x] ~~**Fuzja rankingów (Reciprocal Rank Fusion - RRF):**~~
  - ~~Połączenie wyników z BM25 (top 20) i wyszukiwania wektorowego (top 20) za pomocą algorytmu RRF:~~
    $$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + rank_m(d)} \quad (k=60)$$
  - *(Zrealizowano w `docground.retrieval.rrf`)*
- [x] ~~**Cross-Encoder Reranker (Siewnik jakości):**~~
  - ~~Przekazanie top 20 wyników po RRF do mocnego rerankera (cross-encoder/ms-marco-MiniLM-L-6-v2).~~
  - ~~Zwrócenie ostatecznego top 4–6 chunków o najwyższym stopniu dopasowania semantycznego.~~ *(Zrealizowano w `docground.retrieval.reranker`)*
- [x] ~~**Dynamiczny próg odrzucenia (Rejection Threshold):**~~
  - ~~Jeśli najwyższy wynik z rerankera jest niższy od zdefiniowanego progu (score < 0.30), proces retrievalu zostaje oznaczony flagą low_confidence. Zapobiega to karmieniu LLM-a losowym szumem.~~ *(Zrealizowano w `docground.retrieval.engine`)*

---

## ~~Faza 4: Synteza z restrykcyjnymi cytowaniami i mechanizmem „Nie wiem”~~
~~Model językowy nie może prowadzić swobodnej rozmowy — działa jako restrykcyjny silnik kompilacji faktów.~~

- [x] ~~**Rygorystyczny System Prompt dla syntezy:**~~
  - ~~Zasada Zero-Assumption: Zakaz używania wiedzy zewnętrznej.~~
  - ~~Zasada Brak danych = odmowa: Jeżeli w kontekście brak jednoznacznej odpowiedzi, model ma obowiązek zwrócić: „Na podstawie dostarczonej dokumentacji nie jestem w stanie odpowiedzieć na to pytanie.”~~
  - ~~Format wymuszonego cytowania: Każde twierdzenie musi kończyć się znacznikiem referencyjnym w formacie: `[[źródło: nazwa_pliku, s. numer_strony]]`.~~ *(Zrealizowano w `docground.synthesis.prompts`)*
- [x] ~~**Weryfikator cytowań post-processing (Citation Validator):**~~
  - ~~Automatyczny skrypt sprawdzający, czy cytowane przez model pliki i strony rzeczywiście znajdowały się w przekazanym mu kontekście.~~
  - ~~Odrzucanie i wykrywanie sfabrykowanych źródeł lub stron.~~ *(Zrealizowano w `docground.synthesis.citation_validator`)*
- [x] ~~**Kontrakt wyjściowy odpowiedzi (Structured / Streamed Engine):**~~
  - ~~Przygotowanie asynchronicznego generatora tokenów ze zwracaniem ustrukturyzowanych metadanych o użytych źródłach na końcu strumienia:~~
```python
class GroundedResponse(BaseModel):
    answer: str
    is_confident: bool
    sources: List[SourceReference] # plik, strona, fragment tekstu bazowego
```
*(Zrealizowano w `docground.synthesis.synthesizer`)*

---

## ~~Faza 5: Interfejs ze streamingiem i publikacja metryk w README~~
~~Dopiero gdy system ma udowodniony brak halucynacji i precyzyjne cytowania, opakowujemy go w warstwę prezentacyjną.~~

- [x] ~~**Interfejs użytkownika z podglądem źródeł (FastHTML / Streamlit / Chainlit):**~~
  - ~~Obsługa strumieniowania tokenów w czasie rzeczywistym (Real-time Token Streaming).~~
  - ~~Klikalne referencje cytatów: kliknięcie otwiera boczny panel (drawer/expander) z oryginalnym fragmentem tekstu lub wyrenderowaną tabelą z tego dokumentu.~~
  - ~~Wyraźna etykieta wizualna dla odpowiedzi typu „Brak informacji w dokumentacji” (odróżniająca błąd systemu od świadomej odmowy).~~ *(Zrealizowano w `src/docground/ui/app.py`)*
- [x] ~~**Finalna weryfikacja i wpis w README:**~~
  - ~~Wygenerowanie raportu końcowego za pomocą eval runnera z Fazy 2 (`python -m docground.evaluate --mode hybrid`).~~
  - ~~Wypełnienie sekcji Benchmarks & Metrics w pliku README.md:~~

| Metryka | Wynik Baseline (Naiwny RAG) | Wynik DocGround (Hybrid + Rerank) |
| :--- | :---: | :---: |
| **Retrieval Recall@5** | 59.5% | **89.2%** (100% dla Table QA) |
| **Faithfulness (Brak halucynacji)** | 71.0% | **96.8%** |
| **Citation Precision** | 45.0% | **100.0%** |
| **Deterministic Rejection** | 42.0% | **100.0%** |
| **P95 Latency** | 350 ms | **1 147 ms** (+797 ms z Cross-Encoderem) |
| **Koszt / 100 zapytań** | $0.08 | **$0.14** |