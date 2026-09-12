"""Dense Vector Indexer oparty na FastEmbed / SentenceTransformers z podobieństwem cosinusowym i filtrowaniem po metadanych."""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from fastembed import TextEmbedding
from docground.models import DocumentChunk
from docground.config import settings


class DenseRetriever:
    def __init__(self, chunks: List[DocumentChunk], model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.chunks = chunks
        self.model_name = model_name
        print(f"[DenseRetriever] Ładowanie modelu embeddingów: {model_name}...")
        self.embedding_model = TextEmbedding(model_name=model_name)
        
        # Wygenerowanie embeddingów dla wszystkich chunków (z uwzględnieniem tagów semantycznych)
        contents = []
        for c in chunks:
            tags_hdr = c.metadata.get("tags_header", "") if c.metadata else ""
            prefix = f"[{tags_hdr}] " if tags_hdr else ""
            contents.append(f"{c.doc_name} (strona {c.page_number}) {prefix}: {c.content}")
        embeddings_list = list(self.embedding_model.embed(contents))
        self.doc_embeddings = np.array(embeddings_list, dtype=np.float32)
        # Normalizacja L2 do szybkiego obliczania cosinusowego jako iloczyn skalarny
        norms = np.linalg.norm(self.doc_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        self.doc_embeddings = self.doc_embeddings / norms
        print(f"[DenseRetriever] Zindeksowano {len(chunks)} wektorów o wymiarze {self.doc_embeddings.shape[1]}")

    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        query_embed = list(self.embedding_model.query_embed(query))[0]
        q_vec = np.array(query_embed, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scores = np.dot(self.doc_embeddings, q_vec)

        # Sortowanie malejące
        sorted_indices = np.argsort(scores)[::-1]

        results: List[Tuple[DocumentChunk, float]] = []
        for idx in sorted_indices:
            ch = self.chunks[idx]
            # Opcjonalne filtrowanie po metadanych
            if filters:
                match = True
                for k, v in filters.items():
                    if getattr(ch, k, None) != v and ch.metadata.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            results.append((ch, float(scores[idx])))
            if len(results) >= top_k:
                break

        return results
