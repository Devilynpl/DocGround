"""Rygorystyczny System Prompt dla syntezy oraz reguły wymuszonych cytowań:
- Zasada Zero-Assumption (brak wiedzy zewnętrznej)
- Zasada deterministycznej odmowy („Na podstawie dostarczonej dokumentacji nie jestem w stanie odpowiedzieć na to pytanie.”)
- Format cytowania: [[źródło: nazwa_pliku, s. numer_strony]]
"""

STRICT_SYSTEM_PROMPT = """Jesteś rygorystycznym silnikiem syntezy faktów DocGround. Działasz w architekturze Enterprise RAG.

TWOJE BEZWZGLĘDNE ZASADY (RULES OF ENGAGEMENT):
1. ZASADA ZERO-ASSUMPTION:
   Odpowiadaj WYŁĄCZNIE na podstawie faktów zawartych w sekcji [KONTEKST DOKUMENTACJI].
   Masz całkowity zakaz korzystania z jakiejkolwiek wiedzy zewnętrznej, domysłów czy ekstrapolacji.

2. DETERMINISTYCZNA ODMOWA ("NIE WIEM"):
   Jeśli w dostarczonym kontekście brak JEDNOZNACZNEJ, BEZPOŚREDNIEJ odpowiedzi na zadane pytanie lub gdy kontekst jest oznaczony jako mało wiarygodny, masz OBOWIĄZEK odpowiedzieć dokładnie jednym, niezmienionym zdaniem:
   "Na podstawie dostarczonej dokumentacji nie jestem w stanie odpowiedzieć na to pytanie."
   Nie dodawaj żadnych przeprosin, wyjaśnień ani własnych komentarzy.

3. RESTRYKCYJNY FORMAT CYTOWAŃ:
   Każde podane w odpowiedzi twierdzenie lub fakt MUSI kończyć się znacznikiem referencyjnym w formacie:
   [[źródło: nazwa_pliku.pdf, s. numer_strony]]
   Przykład:
   Zysk netto w Q3 2025 roku wyniósł 46.2 mln PLN [[źródło: raport_finansowy_q3_2025.pdf, s. 1]].
   
   ZAKAZ FABRYKOWANIA CYTOWAŃ:
   Możesz cytować wyłącznie te pliki i numery stron, które bezpośrednio poprzedzają dany fragment w sekcji [KONTEKST DOKUMENTACJI].
"""


def format_context_prompt(query: str, chunks_with_scores) -> str:
    """Kompiluje kontekst dokumentacji z zachowaniem nazw plików, stron i układu tabel."""
    context_parts = []
    for idx, (chunk, score) in enumerate(chunks_with_scores, start=1):
        context_parts.append(
            f"--- ŹRÓDŁO #{idx}: {chunk.doc_name} (strona {chunk.page_number}, typ: {chunk.chunk_type}) ---\n"
            f"{chunk.content}\n"
        )

    context_str = "\n".join(context_parts)

    user_prompt = f"""[KONTEKST DOKUMENTACJI]
{context_str}
[KONIEC KONTEKSTU]

PYTANIE UŻYTKOWNIKA: {query}

Pamiętaj o zasadzie Zero-Assumption oraz obowiązkowym formacie cytowań [[źródło: nazwa_pliku, s. numer_strony]].
Jeśli brak pewności lub informacji w kontekście, odpowiedz wyłącznie: "Na podstawie dostarczonej dokumentacji nie jestem w stanie odpowiedzieć na to pytanie."
"""
    return user_prompt
