"""Section retrieval: BM25 and/or dense over chunks, folded to sections, fused with RRF.

    r = load_retriever()                       # dense part only if data/index/ exists
    hits = r.search("ขี่มอไซค์ไม่ใส่หมวก", k=5)    # mode "hybrid" | "bm25" | "dense"

Scores from BM25 and cosine are on different scales, so the two lists are fused by rank
(Reciprocal Rank Fusion, k=60): score = sum over modes of 1 / (60 + rank).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..schemas import PenaltyRule, Section
from .bm25 import BM25Index
from .chunks import Chunk, make_chunks
from .dense import Embedder, VectorIndex
from .legal_terms import expand
from .offenses import OffenseDoc, build_offense_docs

RRF_K = 60
POOL = 50          # how many chunks each mode contributes before fusion


@dataclass
class Hit:
    section: Section
    score: float
    best_chunk: str
    ranks: dict[str, int] = field(default_factory=dict)   # mode -> 1-based section rank

    @property
    def key(self) -> str:
        return self.section.key


class Retriever:
    def __init__(self, sections: list[Section], *, chunks: list[Chunk] | None = None,
                 vectors: VectorIndex | None = None, embedder: Embedder | None = None,
                 rules: dict[str, PenaltyRule] | None = None):
        self.sections = {s.key: s for s in sections}
        self.rules = rules or {}
        self.offense_docs: list[OffenseDoc] = build_offense_docs(self.rules, sections) if rules else []
        self._offense_bm25 = None
        if self.offense_docs:
            from rank_bm25 import BM25Okapi

            from .tokenize import tokenize
            self._offense_bm25 = BM25Okapi([tokenize(d.text) or ["_"] for d in self.offense_docs])
        self._offense_vecs = (embedder.encode([d.text for d in self.offense_docs], kind="passage")
                              if embedder is not None and vectors is not None and self.offense_docs else None)
        self.chunks = chunks or make_chunks(sections)
        self.bm25 = BM25Index(self.chunks)
        self.vectors = vectors
        self.embedder = embedder
        if vectors is not None:
            have = {c.key for c in self.chunks}
            missing = [k for k in vectors.chunk_keys if k not in have]
            if missing:
                raise ValueError(f"dense index is stale ({len(missing)} unknown chunks): rebuild it "
                                 "with scripts/build_index.py")
            pos = {c.key: i for i, c in enumerate(self.chunks)}
            self._vec_to_chunk = [pos[k] for k in vectors.chunk_keys]

    @property
    def has_dense(self) -> bool:
        return self.vectors is not None and self.embedder is not None

    # -------------------------------------------------------------- per-mode rankings
    def _fold(self, chunk_hits: list[tuple[int, float]], docs: set[str] | None):
        """chunk hits -> [(section_key, score, best chunk text)] keeping each section's best chunk."""
        best: dict[str, tuple[float, str]] = {}
        for ci, sc in chunk_hits:
            c = self.chunks[ci]
            if docs and c.section_key.split(":")[0] not in docs:
                continue
            if c.section_key not in best or sc > best[c.section_key][0]:
                best[c.section_key] = (sc, c.text)
        return sorted(((k, s, t) for k, (s, t) in best.items()), key=lambda x: -x[1])

    def rank_bm25(self, query: str, docs=None, *, use_expansion: bool = True):
        q = expand(query) if use_expansion else query
        return self._fold(self.bm25.search(q, POOL), docs)

    def rank_dense(self, query: str, docs=None):
        if not self.has_dense:
            return []
        qv = self.embedder.encode([query], kind="query")[0]
        hits = [(self._vec_to_chunk[i], s) for i, s in self.vectors.search(qv, POOL)]
        return self._fold(hits, docs)

    # -------------------------------------------------------------- public
    def search(self, query: str, k: int = 8, *, mode: str = "hybrid",
               docs: set[str] | None = None, use_expansion: bool = True) -> list[Hit]:
        if mode == "dense" and not self.has_dense:
            raise RuntimeError("no dense index loaded: run scripts/build_index.py first")
        lists: dict[str, list] = {}
        if mode in ("bm25", "hybrid"):
            lists["bm25"] = self.rank_bm25(query, docs, use_expansion=use_expansion)
        if mode in ("dense", "hybrid") and self.has_dense:
            lists["dense"] = self.rank_dense(query, docs)

        fused: dict[str, Hit] = {}
        for name, ranked in lists.items():
            for r, (key, score, text) in enumerate(ranked, start=1):
                h = fused.get(key)
                if h is None:
                    h = fused[key] = Hit(section=self.sections[key], score=0.0, best_chunk=text)
                h.ranks[name] = r
                h.score += 1 / (RRF_K + r) if len(lists) > 1 else score
        return sorted(fused.values(), key=lambda h: -h.score)[:k]


    # -------------------------------------------------------------- offense catalogue
    def score_offenses(self, query: str, *, use_expansion: bool = True) -> list[tuple[PenaltyRule, float]]:
        """Raw BM25 score of every catalogue offense, best first (used by the classic RAG's
        min_score floor -- RRF scores are rank-only and cannot carry a floor)."""
        if self._offense_bm25 is None:
            raise RuntimeError("no penalty table loaded")
        from .tokenize import tokenize

        toks = tokenize(expand(query) if use_expansion else query)
        sc = self._offense_bm25.get_scores(toks) if toks else [0.0] * len(self.offense_docs)
        order = sorted(range(len(sc)), key=lambda i: -sc[i])
        return [(self.rules[self.offense_docs[i].offense_id], float(sc[i])) for i in order]

    def search_offenses(self, query: str, k: int = 8, *, mode: str = "hybrid",
                        use_expansion: bool = True) -> list[tuple[PenaltyRule, float, dict[str, int]]]:
        """Candidate offenses for a story: [(rule, fused score, {mode: rank})], best first."""
        if self._offense_bm25 is None:
            raise RuntimeError("no penalty table loaded")
        from .tokenize import tokenize

        lists: dict[str, list[int]] = {}
        if mode in ("bm25", "hybrid"):
            toks = tokenize(expand(query) if use_expansion else query)
            sc = self._offense_bm25.get_scores(toks) if toks else []
            lists["bm25"] = [i for i in sorted(range(len(sc)), key=lambda i: -sc[i]) if sc[i] > 0]
        if mode in ("dense", "hybrid") and self._offense_vecs is not None:
            qv = self.embedder.encode([query], kind="query")[0]
            sims = self._offense_vecs @ qv
            lists["dense"] = sorted(range(len(sims)), key=lambda i: -sims[i])
        if mode == "dense" and "dense" not in lists:
            raise RuntimeError("no dense index loaded: run scripts/build_index.py first")
        fused: dict[int, list] = {}
        for name, order in lists.items():
            for r, i in enumerate(order, start=1):
                f = fused.setdefault(i, [0.0, {}])
                f[0] += 1 / (RRF_K + r)
                f[1][name] = r
        ranked = sorted(fused.items(), key=lambda x: -x[1][0])[:k]
        return [(self.rules[self.offense_docs[i].offense_id], sc, ranks) for i, (sc, ranks) in ranked]


def load_retriever(sections_path: Path | None = None, index_dir: Path | None = None,
                   *, with_dense: bool = True) -> Retriever:
    """Corpus from data/processed/sections.jsonl; dense part only if data/index/ exists."""
    from ..config import INDEX_DIR, SECTIONS_PATH, get_settings

    sections_path = sections_path or SECTIONS_PATH
    index_dir = index_dir or INDEX_DIR
    if not sections_path.exists():
        raise FileNotFoundError(f"{sections_path} missing: run scripts/build_corpus.py first")
    sections = [Section.model_validate_json(l) for l in sections_path.read_text(encoding="utf-8").splitlines() if l]
    vectors = embedder = None
    if with_dense and (index_dir / "meta.json").exists():
        from .dense import SentenceTransformerEmbedder

        vectors = VectorIndex.load(index_dir)
        name = get_settings().embed_model
        if vectors.model != name:
            raise ValueError(f"index was built with {vectors.model} but EMBED_MODEL is {name}")
        embedder = SentenceTransformerEmbedder(name)
    from ..config import PENALTIES_PATH
    from ..data.penalties import load_penalties

    rules = load_penalties() if PENALTIES_PATH.exists() else None
    return Retriever(sections, vectors=vectors, embedder=embedder, rules=rules)
