"""Embed every chunk of the corpus -> data/index/ (vectors.npy + meta.json).

    python scripts/build_index.py                       # EMBED_MODEL from .env (default BAAI/bge-m3)
    python scripts/build_index.py --model intfloat/multilingual-e5-small --out data/index_e5

Downloads the model once (bge-m3 is ~2.3 GB; multilingual-e5-small ~0.5 GB and faster on CPU).
The app embeds queries with the model recorded in meta.json, so EMBED_MODEL must match it.
Rebuild after every scripts/build_corpus.py run: a stale index is refused at load time.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traffic_law.config import INDEX_DIR, SECTIONS_PATH, get_settings  # noqa: E402
from traffic_law.retrieval.chunks import make_chunks  # noqa: E402
from traffic_law.retrieval.dense import SentenceTransformerEmbedder, build_vector_index  # noqa: E402
from traffic_law.schemas import Section  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=get_settings().embed_model)
    ap.add_argument("--out", type=Path, default=INDEX_DIR)
    args = ap.parse_args()

    sections = [Section.model_validate_json(l) for l in SECTIONS_PATH.read_text(encoding="utf-8").splitlines() if l]
    chunks = make_chunks(sections)
    print(f"{len(sections)} sections -> {len(chunks)} chunks; loading {args.model} ...")
    t = time.time()
    emb = SentenceTransformerEmbedder(args.model)
    index = build_vector_index(chunks, emb)
    index.save(args.out)
    print(f"wrote {args.out} ({index.vectors.shape[0]} x {index.vectors.shape[1]}) in {time.time() - t:.0f}s")


if __name__ == "__main__":
    main()
