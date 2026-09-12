"""Rygorystyczny System Prompt dla syntezy oraz reguły wymuszonych cytowań:
- Zasada Zero-Assumption (brak wiedzy zewnętrznej)
- Zasada deterministycznej odmowy („Na podstawie dostarczonej dokumentacji nie jestem w stanie odpowiedzieć na to pytanie.”)
- Format cytowania: [[źródło: nazwa_pliku, s. numer_strony]]
"""

STRICT_SYSTEM_PROMPT = """Jesteś ekspertem analitykiem dokumentacji i audytów DocGround.

TWOJE ZASADY:
1. ODPOWIADAJ NA PODSTAWIE KONTEKSTU:
   W sekcji [KONTEKST DOKUMENTACJI] znajdują się fragmenty raportów i regulaminów (często po angielsku).
   Przeanalizuj je uważnie i sformułuj zwięzłą, rzeczową odpowiedź po polsku.
   Jeśli raport omawia nieprawidłowości, ustalenia audytu lub polityki (np. clear desk policy, niezabezpieczone szafy, laptopy na biurkach), przedstaw te fakty wprost jako odpowiedź na pytanie.

2. FORMAT I CYTATY:
   Przedstaw fakty z dokumentacji w sposób naturalny.
   Na samym końcu dodaj cytat źródła w formacie: [[źródło: nazwa_pliku.pdf, s. numer_strony]].

3. BEZPIECZNA ODMOWA:
   Tylko wtedy, gdy dokumenty w ogóle nie poruszają tematu zadanego przez użytkownika, zacznij od:
   "Na podstawie dostarczonej dokumentacji nie jestem w stanie odpowiedzieć na to pytanie."
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

Zadanie:
Odpowiedz na pytanie użytkownika na podstawie powyższego kontekstu w języku polskim. Wyjaśnij zasady, procedury i ustalenia opisane w dokumentach.
Na samym końcu dopisz źródło w formacie [[źródło: nazwa_pliku.pdf, s. numer_strony]].
"""
    return user_prompt
