"""Dense retrieval: an embedding model + a numpy cosine index saved under data/index/.

The embedder is a small protocol so tests can use a fake one; the real one wraps
sentence-transformers and is imported only when used. e5 models need "query: " /
"passage: " prefixes; bge-m3 needs none.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import numpy as np

from .chunks import Chunk


class Embedder(Protocol):
    name: str

    def encode(self, texts: list[str], *, kind: str) -> np.ndarray:  # kind: "query" | "passage"
        ...


class SentenceTransformerEmbedder:
    def __init__(self, name: str, batch_size: int = 16):
        from sentence_transformers import SentenceTransformer

        self.name = name
        self.batch_size = batch_size
        self._model = SentenceTransformer(name)
        self._e5 = "e5" in name.lower()

    def encode(self, texts: list[str], *, kind: str) -> np.ndarray:
        if self._e5:
            texts = [f"{kind}: {t}" for t in texts]
        v = self._model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                               show_progress_bar=len(texts) > 64)
        return np.asarray(v, dtype=np.float32)


@dataclass
class VectorIndex:
    vectors: np.ndarray        # (n_chunks, dim), L2-normalised
    chunk_keys: list[str]
    model: str

    def search(self, qvec: np.ndarray, k: int = 50) -> list[tuple[int, float]]:
        sims = self.vectors @ qvec.reshape(-1)
        order = np.argsort(-sims)[:k]
        return [(int(i), float(sims[i])) for i in order]

    # ---- persistence: vectors.npy + meta.json (model name, chunk keys, build time)
    def save(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        np.save(folder / "vectors.npy", self.vectors)
        meta = {"model": self.model, "dim": int(self.vectors.shape[1]), "n": len(self.chunk_keys),
                "chunk_keys": self.chunk_keys, "built_at": datetime.now(timezone.utc).isoformat()}
        (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, folder: Path) -> "VectorIndex":
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        return cls(vectors=np.load(folder / "vectors.npy"), chunk_keys=meta["chunk_keys"], model=meta["model"])


def build_vector_index(chunks: list[Chunk], embedder: Embedder) -> VectorIndex:
    vecs = embedder.encode([c.text for c in chunks], kind="passage")
    return VectorIndex(vectors=vecs, chunk_keys=[c.key for c in chunks], model=embedder.name)
