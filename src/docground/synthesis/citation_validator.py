"""Post-Processing Citation Validator:
Automatyczny skrypt weryfikujący czy cytowane przez model pliki i strony rzeczywiście
znajdowały się w przekazanym kontekście i czy nie zostały sfabrykowane.
"""

import re
from typing import List, Tuple, Dict, Any, Optional
from docground.models import DocumentChunk, SourceReference

# Format cytowania: [[źródło: nazwa_pliku.pdf, s. 1]]
CITATION_REGEX = re.compile(r"\[\[(?:źródło|source):\s*([a-zA-Z0-9_\-\.]+),\s*(?:s\.|strona|p\.)\s*(\d+)\]\]", re.IGNORECASE)


class CitationValidator:
    def __init__(self):
        pass

    def extract_citations(self, text: str) -> List[Tuple[str, int]]:
        """Ekstrahuje listę par (doc_name, page_number) z wygenerowanej odpowiedzi."""
        matches = CITATION_REGEX.findall(text)
        citations = []
        for doc_name, page_str in matches:
            try:
                citations.append((doc_name.strip(), int(page_str.strip())))
            except ValueError:
                continue
        return citations

    def validate_citations(
        self,
        answer_text: str,
        provided_chunks: List[DocumentChunk]
    ) -> Tuple[bool, List[SourceReference], str]:
        """Sprawdza poprawność cytowań w stosunku do dostarczonych chunków.
        Zwraca (is_all_valid, verified_sources, sanitized_answer).
        """
        raw_citations = self.extract_citations(answer_text)
        if not raw_citations:
            # Odpowiedź bez cytowań (np. odmowa 'Nie wiem')
            return True, [], answer_text

        # Zbiór poprawnych (doc_name, page_number) z przekazanego kontekstu
        valid_contexts = {(c.doc_name, c.page_number): c for c in provided_chunks}

        verified_sources: List[SourceReference] = []
        all_valid = True

        for doc_name, page_num in raw_citations:
            if (doc_name, page_num) in valid_contexts:
                matched_chunk = valid_contexts[(doc_name, page_num)]
                verified_sources.append(
                    SourceReference(
                        doc_name=doc_name,
                        page_number=page_num,
                        quote_snippet=matched_chunk.raw_context_anchor,
                        chunk_id=matched_chunk.chunk_id,
                        is_verified=True
                    )
                )
            else:
                # Wykryto sfabrykowane źródło lub stronę
                all_valid = False
                verified_sources.append(
                    SourceReference(
                        doc_name=doc_name,
                        page_number=page_num,
                        quote_snippet="[FABRYKACJA: Źródło lub strona nie istniały w przekazanym kontekście]",
                        chunk_id=None,
                        is_verified=False
                    )
                )

        return all_valid, verified_sources, answer_text
