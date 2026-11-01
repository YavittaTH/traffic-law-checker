"""Try retrieval on any story from the command line.

    python scripts/search.py "ขี่มอไซค์ไม่ใส่หมวกแล้วฝ่าไฟแดง"
    python scripts/search.py "ขับรถคุยโทรศัพท์" --mode bm25 --no-expand -k 5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traffic_law.retrieval.legal_terms import expansions  # noqa: E402
from traffic_law.retrieval.retriever import load_retriever  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--mode", default="hybrid", choices=["hybrid", "bm25", "dense"])
    ap.add_argument("--no-expand", action="store_true")
    args = ap.parse_args()

    r = load_retriever(with_dense=args.mode != "bm25")
    mode = args.mode if (r.has_dense or args.mode == "bm25") else "bm25"
    if mode != args.mode:
        print("(no dense index yet: using bm25 — run scripts/build_index.py)")
    if not args.no_expand:
        print("term table added:", " | ".join(expansions(args.query)) or "-")

    print(f"\nOffenses ({mode})")
    for rule, score, ranks in r.search_offenses(args.query, k=args.k, mode=mode, use_expansion=not args.no_expand):
        print(f"  {score:7.4f}  {rule.offense_id:22} {rule.description}  ranks={ranks}")
    print(f"\nSections ({mode})")
    for h in r.search(args.query, k=args.k, mode=mode, use_expansion=not args.no_expand):
        print(f"  {h.score:7.4f}  {h.section.label[:60]}  ranks={h.ranks}")
        print("           " + h.best_chunk.replace("\n", " ")[:140])


if __name__ == "__main__":
    main()
