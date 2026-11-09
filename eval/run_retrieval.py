"""Retrieval evaluation: which modes put the right sections in the top k?

    python eval/run_retrieval.py                               # dev set, every mode available
    python eval/run_retrieval.py --gold eval/scenarios.jsonl --out eval/results_retrieval

Modes: bm25_raw (no term table), bm25 (with legal_terms expansion), dense, hybrid.
dense / hybrid run only when data/index/ exists (scripts/build_index.py).
Writes report.md (metric table) and per_query.md (top-5 sections per query, misses marked).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traffic_law.config import EVAL_DIR, PROJECT_ROOT  # noqa: E402
from traffic_law.data.penalties import load_penalties, offense_section_keys  # noqa: E402
from traffic_law.evaluation import (all_found_at_k, bootstrap_ci, freeze_status,  # noqa: E402
                                    load_gold, recall_at_k, reciprocal_rank)
from traffic_law.retrieval.retriever import load_retriever  # noqa: E402

KS = (1, 3, 5, 8)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=Path, default=EVAL_DIR / "dev_retrieval.jsonl")
    ap.add_argument("--out", type=Path, default=EVAL_DIR / "results_retrieval")
    ap.add_argument("--no-dense", action="store_true")
    ap.add_argument("--index", type=Path, default=None, help="dense index folder (default data/index/)")
    args = ap.parse_args()

    rules = load_penalties()
    r = load_retriever(index_dir=args.index, with_dense=not args.no_dense)
    gold = [g for g in load_gold(args.gold) if offense_section_keys(g.get("expected", []), rules)]
    modes = ["bm25_raw", "bm25"] + (["dense", "hybrid"] if r.has_dense else [])

    def ranked(mode: str, q: str) -> list[str]:
        if mode == "bm25_raw":
            return [h.key for h in r.search(q, k=20, mode="bm25", use_expansion=False)]
        return [h.key for h in r.search(q, k=20, mode=mode)]

    rows, per_query = [], []
    for mode in modes:
        rec = {k: [] for k in KS}
        allk = {k: [] for k in KS}
        rr = []
        for g in gold:
            rel = offense_section_keys(g["expected"], rules)
            got = ranked(mode, g["scenario"])
            for k in KS:
                rec[k].append(recall_at_k(got, rel, k))
                allk[k].append(1.0 if all_found_at_k(got, rel, k) else 0.0)
            rr.append(reciprocal_rank(got, rel))
            if mode in (modes[-1], "bm25_raw"):
                per_query.append((mode, g, rel, got[:5]))
        lo, hi = bootstrap_ci(rec[5])
        rows.append((mode, *[sum(rec[k]) / len(gold) for k in KS], sum(allk[5]) / len(gold),
                     sum(rr) / len(gold), lo, hi))

    head = "| mode | " + " | ".join(f"recall@{k}" for k in KS) + " | all-found@5 | MRR | recall@5 95% CI |"
    sep = "|" + "---|" * (len(KS) + 5)
    lines = [f"# Retrieval — {args.gold.name} ({len(gold)} queries)", "",
             f"dense index: {'yes (' + r.vectors.model + ')' if r.has_dense else 'not built'}", "",
             "tuning freeze: " + " · ".join(freeze_status(PROJECT_ROOT)), "", head, sep]
    for m, *vals, lo, hi in rows:
        lines.append(f"| {m} | " + " | ".join(f"{v:.1%}" if i < len(KS) + 1 else f"{v:.3f}"
                                             for i, v in enumerate(vals)) + f" | {lo:.0%}–{hi:.0%} |")
    # ---- offense level: are the expected offenses among the top-k candidate offenses?
    og = [g for g in load_gold(args.gold) if g.get("expected")]
    lines += ["", f"## Offense catalogue ({len(og)} queries)", "",
              "| mode | recall@1 | recall@3 | recall@5 | all-found@5 | MRR | recall@5 95% CI |", "|---|---|---|---|---|---|---|"]
    for mode in modes:
        rec = {k: [] for k in (1, 3, 5)}
        allf, rr = [], []
        for g in og:
            exp = set(g["expected"])
            if mode == "bm25_raw":
                got = [x[0].offense_id for x in r.search_offenses(g["scenario"], k=20, mode="bm25", use_expansion=False)]
            else:
                got = [x[0].offense_id for x in r.search_offenses(g["scenario"], k=20, mode=mode)]
            for k in rec:
                rec[k].append(recall_at_k(got, exp, k))
            allf.append(1.0 if all_found_at_k(got, exp, 5) else 0.0)
            rr.append(reciprocal_rank(got, exp))
            if mode == modes[-1]:
                miss = exp - set(got[:5])
                per_query.append(("offense:" + mode, g, exp, got[:5]))
        lo, hi = bootstrap_ci(rec[5])
        n = len(og)
        lines.append(f"| {mode} | {sum(rec[1])/n:.1%} | {sum(rec[3])/n:.1%} | {sum(rec[5])/n:.1%} | "
                     f"{sum(allf)/n:.1%} | {sum(rr)/n:.3f} | {lo:.0%}–{hi:.0%} |")
    report = "\n".join(lines) + "\n"

    pq = [f"# Per query (modes: bm25_raw and {modes[-1]})", ""]
    for mode, g, rel, top in per_query:
        short = lambda k: k.split(":")[-1]
        miss = rel - set(top)
        mark = "✓" if not miss else "✗ missing " + ", ".join(sorted(short(k) for k in miss))
        pq.append(f"- **{g['id']}** [{mode}] {g['scenario']}  \n  expected {sorted(short(k) for k in rel)} "
                  f"→ top5 {[short(k) for k in top]} {mark}")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.md").write_text(report, encoding="utf-8")
    (args.out / "per_query.md").write_text("\n".join(pq) + "\n", encoding="utf-8")
    print(report)
    print(f"wrote {args.out}/report.md and per_query.md")


if __name__ == "__main__":
    main()
