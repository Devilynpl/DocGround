"""Query Expansion & Bilingual Translation Module:
Automatycznie rozwija potoczne polskie zapytania na synonimy i odpowiedniki angielskie,
umożliwiając wyszukiwanie hybrydowe (BM25 + Dense) w dokumentach anglojęzycznych.
"""

from typing import Optional

# Prosty, deterministyczny słownik pojęciowy dla najczęstszych domen biznesowych, szkolnych i technicznych
CONCEPT_MAPPINGS = {
    "obiad": "lunch meals food school meal provision",
    "obiady": "lunch meals food school meal provision",
    "posiłek": "meals lunch",
    "posiłki": "meals lunch",
    "szkoł": "school head teacher staff education",
    "nauczyciel": "teacher staff employee",
    "nauczyciele": "teacher staff employee",
    "dyrektor": "head headteacher management",
    "bieda": "poverty poor deprivation chronic poverty",
    "biedy": "poverty poor deprivation chronic poverty",
    "pokolenia": "intergenerational transmission IGT generations",
    "pokoleniach": "intergenerational transmission IGT generations",
    "laptopy": "laptops computer equipment assets",
    "kradzież": "theft stolen security breach break-in",
    "biuro": "office West Offices Hazel Court building",
    "biura": "office West Offices Hazel Court building",
    "wieżowce": "tall buildings skyscrapers high-rise urban living",
    "wieżowiec": "tall buildings skyscrapers high-rise urban living",
    "bristol": "bristol local plan urban living spd",
    "mieszkania": "homes housing residential development",
    "szkolenie": "training safer recruitment course",
    "szkolenia": "training safer recruitment course",
    "slajd": "slide slides presentation powerpoint font",
    "slajdy": "slide slides presentation powerpoint font",
    "prezentacja": "presentation powerpoint font size design",
    "czcionka": "font sans-serif verdana size points",
    "prowizja": "commission fee margin interchange",
    "karta": "card debit credit visa mastercard",
    "błąd": "error code status",
    "ubezpieczenie": "insurance policy claim owu",
    "zalanie": "water damage flooding claim",
    "pojazd": "vehicle car automobile",
}


def expand_query(query: str, llm_instance: Optional[object] = None) -> str:
    """Rozwija zapytanie użytkownika o terminy angielskie i synonimy,
    aby retriever (BM25 i model embeddingów) bez problemu znalazł dokumenty w języku angielskim.
    """
    q_lower = query.lower()
    expanded_terms = []

    # 1. Regułowe mapowanie pojęć (błyskawiczne < 1ms)
    for trigger, expansion in CONCEPT_MAPPINGS.items():
        if trigger in q_lower:
            expanded_terms.append(expansion)

    # 2. Opcjonalne użycie lokalnego LLM jeśli dostępne i brak prostych dopasowań
    if llm_instance and not expanded_terms and len(query.strip()) > 5:
        try:
            # Krótki prompt dla LLM do ekstrakcji słów kluczowych EN
            prompt = (
                f"<|im_start|>system\nYou are a search query translator. "
                f"Translate the following user question into 3-5 English search keywords for document search. Output ONLY the keywords separated by spaces.<|im_end|>\n"
                f"<|im_start|>user\n{query}<|im_end|>\n<|im_start|>assistant\n"
            )
            res = llm_instance(prompt, max_tokens=25, stop=["\n", "<|im_end|>"], temperature=0.1)
            keywords = res["choices"][0]["text"].strip()
            if keywords:
                expanded_terms.append(keywords)
        except Exception:
            pass

    if expanded_terms:
        # Zwracamy połączone zapytanie: oryginalne + przetłumaczone słowa kluczowe
        combined_expansion = " ".join(set(" ".join(expanded_terms).split()))
        return f"{query} {combined_expansion}"

    return query
