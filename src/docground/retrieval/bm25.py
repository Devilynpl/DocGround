"""Sparse BM25 Indexer zachowujący kody błędów, artykuły prawne, cyfry i słowa kluczowe."""

import re
import json
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from docground.models import DocumentChunk
from docground.config import CHUNKS_PATH


STOPWORDS = {
    "czy", "i", "w", "z", "na", "do", "o", "a", "ze", "za", "od", "po", "pod", "dla",
    "to", "co", "jak", "sie", "się", "jest", "są", "sa", "nie", "tak", "że", "ze",
    "oraz", "albo", "lub", "jako", "przez", "przy", "jego", "jej", "ich", "the", "a", "an",
    "in", "on", "at", "to", "for", "of", "and", "or", "is", "are", "be", "with", "by"
}


def tokenize_code_and_legal(text: str) -> List[str]:
    """Tokenizator zachowujący kody np. ERR_0x8004, paragrafy § 1 ust. 2, liczby i słowa (z filtrem stopwords)."""
    # Zamiana znaków specjalnych poza podkreśleniami, paragrafami i kropkami w liczbach
    cleaned = re.sub(r"[^\w\s§_.-]", " ", text.lower())
    tokens = [
        t.strip() for t in cleaned.split() 
        if len(t.strip()) >= 2 and t.strip() not in STOPWORDS
    ]
    return tokens


class BM25Retriever:
    def __init__(self, chunks: List[DocumentChunk]):
        self.chunks = chunks
        self.corpus_tokens = []
        for c in chunks:
            # Łączymy zawartość oraz tagi semantyczne (PL i EN)
            tags = c.metadata.get("semantic_tags", []) if c.metadata else []
            tags_text = " ".join(tags) if tags else ""
            full_text = f"{c.doc_name} {tags_text} {c.content}"
            self.corpus_tokens.append(tokenize_code_and_legal(full_text))
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def search(self, query: str, top_k: int = 20) -> List[Tuple[DocumentChunk, float]]:
        tokens = tokenize_code_and_legal(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        top_indices = scores.argsort()[::-1][:top_k]

        results: List[Tuple[DocumentChunk, float]] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.0:
                results.append((self.chunks[idx], score))
        return results
