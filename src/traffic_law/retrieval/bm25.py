"""BM25 over chunks (rank_bm25.BM25Okapi) with the Thai tokenizer."""
from __future__ import annotations

from .chunks import Chunk
from .tokenize import tokenize


class BM25Index:
    def __init__(self, chunks: list[Chunk], *, k1: float = 1.5, b: float = 0.75):
        from rank_bm25 import BM25Okapi

        self.chunks = chunks
        self._bm25 = BM25Okapi([tokenize(c.text) or ["_"] for c in chunks], k1=k1, b=b)

    def search(self, query: str, k: int = 50) -> list[tuple[int, float]]:
        """(chunk index, score), best first; zero-score chunks are dropped."""
        toks = tokenize(query)
        if not toks:
            return []
        scores = self._bm25.get_scores(toks)
        order = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [(i, float(scores[i])) for i in order if scores[i] > 0]
