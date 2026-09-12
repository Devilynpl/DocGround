"""Semantic Tagger & Metadata Enrichment Module:
Generuje semantyczne tagi (PL + EN) oraz syntetyczne podsumowanie intencji dla każdego chunka,
umożliwiając bezbłędne wyszukiwanie w języku naturalnym.
"""

import re
from typing import List, Dict, Any, Optional
from docground.models import DocumentChunk, ChunkType

# Słownik powiązań pojęciowych dla typowych domen audytowych, technicznych i biznesowych
DOMAIN_TAXONOMY = {
    # Szkoła i edukacja
    "school": ["szkoła", "edukacja", "placówka oświatowa", "oświata"],
    "meals": ["obiady", "posiłki", "stołówka", "wyżywienie", "darmowe obiady"],
    "meal": ["obiady", "posiłki", "stołówka", "wyżywienie", "darmowe obiady"],
    "staff": ["pracownicy", "nauczyciele", "personel", "kadra"],
    "head": ["dyrektor", "kierownictwo", "zarząd"],
    "recruitment": ["rekrutacja", "zatrudnienie", "bezpieczna rekrutacja"],
    "training": ["szkolenie", "kurs", "kwalifikacje"],
    "benefit in kind": ["świadczenie w naturze", "korzyść podatkowa", "podatki", "urząd skarbowy"],
    "data protection": ["ochrona danych", "RODO", "DPA", "bezpieczeństwo danych"],
    
    # Bezpieczeństwo i audyt
    "security": ["bezpieczeństwo", "ochrona", "kontrola"],
    "cupboards": ["szafy", "przechowywanie dokumentów", "zabezpieczenie szaf"],
    "unsecured": ["niezabezpieczony", "otwarty", "ryzyko kradzieży"],
    "theft": ["kradzież", "włamanie", "utrata mienia"],
    "laptops": ["laptopy", "sprzęt komputerowy", "urządzenia mobilne"],
    "incident": ["incydent", "awaria", "zagrożenie"],
    "cert": ["zespół CERT", "reakcja na incydenty"],
    
    # Społeczne i ekonomiczne
    "poverty": ["ubóstwo", "bieda", "wykluczenie społeczne", "niedostatek"],
    "chronic poverty": ["chroniczne ubóstwo", "długotrwała bieda", "dziedziczenie biedy"],
    "intergenerational": ["międzypokoleniowe", "pokolenia", "dziedziczone"],
    "igt": ["transmisja międzypokoleniowa", "ubóstwo dziedziczne"],
    "duration": ["czas trwania", "długość trwania"],
    
    # Prezentacje i technika
    "powerpoint": ["prezentacja", "slajdy", "PowerPoint"],
    "slides": ["slajdy", "układ slajdu", "tworzenie prezentacji"],
    "font": ["czcionka", "krój pisma", "Verdana", "czytelność"],
    "readability": ["czytelność", "wielkość liter", "punkty"],
    
    # Płatności i Cloud
    "blik": ["płatności BLIK", "bramka płatnicza", "transakcje mobilne"],
    "interchange": ["prowizja", "opłata interchange", "koszt transakcji"],
    "api": ["specyfikacja API", "REST API", "integracja"],
    "webhook": ["webhooks", "powiadomienia transakcyjne", "podpis kryptograficzny"],
    "sla": ["dostępność usługi", "gwarancja SLA", "czas reakcji"],
    "cloud": ["chmura", "serwery wirtualne", "cennik cloud"],
}


def extract_semantic_tags(text: str, doc_name: str = "") -> List[str]:
    """Ekstrahuje kluczowe tagi dwujęzyczne (PL i EN) na podstawie zawartości tekstu i nazwy dokumentu."""
    text_lower = f"{doc_name.lower()} {text.lower()}"
    found_tags = set()

    for keyword, pl_synonyms in DOMAIN_TAXONOMY.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", text_lower):
            found_tags.add(keyword)
            found_tags.update(pl_synonyms)

    # Dodaj podstawowe metatagi z nazwy dokumentu
    clean_doc = re.sub(r"[-_.]", " ", doc_name.lower())
    found_tags.update([w for w in clean_doc.split() if len(w) > 3 and not w.isdigit()])

    return sorted(list(found_tags))


def enrich_chunk(chunk: DocumentChunk) -> DocumentChunk:
    """Wzbogaca DocumentChunk o semantyczne tagi w metadanych."""
    tags = extract_semantic_tags(chunk.content, chunk.doc_name)
    enriched_metadata = dict(chunk.metadata or {})
    enriched_metadata["semantic_tags"] = tags
    
    # Tworzymy czytelny nagłówek tagów do indeksowania
    if tags:
        enriched_metadata["tags_header"] = "Tagi: " + ", ".join(tags[:12])
    
    return DocumentChunk(
        chunk_id=chunk.chunk_id,
        doc_name=chunk.doc_name,
        doc_type=chunk.doc_type,
        page_number=chunk.page_number,
        chunk_type=chunk.chunk_type,
        content=chunk.content,
        raw_context_anchor=chunk.raw_context_anchor,
        metadata=enriched_metadata
    )
