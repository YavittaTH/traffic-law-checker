"""Pick the classic RAG's k and min_score floor on the MAIN set, without calling the LLM.

    python eval/run_min_score.py                      # main set -> eval/results_min_score/

For every (k, floor) it measures what the model would be shown:
  context recall     -- gold offenses that made it into the numbered sources (the model can
                        never answer an offense it was not shown, so this caps RAG recall)
  all-in-context     -- violation stories whose whole gold set is in the sources
  mean sources       -- context size (more sources = more distractors for a 4B model)
  refusals           -- stories with no source above the floor (answered out_of_scope without
                        an LLM call), split into right (gold out_of_scope) and wrong (any other)

Selection rule, fixed before looking at the table: keep the highest context recall; among
ties, fewest wrong refusals; then most right refusals; then the smallest mean context.
The naive default is k=8, floor=0 (keep anything with a positive score).
The held-out set is not accepted here.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traffic_law.config import EVAL_DIR, PROJECT_ROOT  # noqa: E402
from traffic_law.evaluation import freeze_status, load_gold  # noqa: E402
from traffic_law.rag import retrieve  # noqa: E402
from traffic_law.retrieval.retriever import load_retriever  # noqa: E402

KS = [3, 4, 6, 8]
FLOORS = [0.0, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]


def evaluate(gold, retriever, k, floor):
    n_gold = hit = all_in = n_viol = 0
    sizes, right_ref, wrong_ref = [], [], []
    for g in gold:
        ids = [s.offense_id for s in retrieve(g["scenario"], retriever, k=k, min_score=floor)]
        sizes.append(len(ids))
        if not ids:
            (right_ref if g["status"] == "out_of_scope" else wrong_ref).append(g["id"])
        if g["expected"]:
            n_viol += 1
            n_gold += len(g["expected"])
            hit += len(set(g["expected"]) & set(ids))
            all_in += set(g["expected"]) <= set(ids)
    return {"k": k, "floor": floor, "context_recall": hit / n_gold, "all_in_context": all_in / n_viol,
            "mean_sources": sum(sizes) / len(sizes), "right_refusals": right_ref, "wrong_refusals": wrong_ref}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=Path, default=EVAL_DIR / "scenarios.jsonl")
    ap.add_argument("--out", type=Path, default=EVAL_DIR / "results_min_score")
    args = ap.parse_args()
    if "heldout" in args.gold.name:
        raise SystemExit("k and min_score are tuned on the main set only")

    gold = load_gold(args.gold)
    retriever = load_retriever(with_dense=False)
    rows = [evaluate(gold, retriever, k, f) for k in KS for f in FLOORS]
    best = max(rows, key=lambda r: (round(r["context_recall"], 6), -len(r["wrong_refusals"]),
                                    len(r["right_refusals"]), -r["mean_sources"]))
    naive = next(r for r in rows if r["k"] == 8 and r["floor"] == 0.0)

    lines = [f"# Classic RAG: k and min_score sweep — {args.gold.name} ({len(gold)} stories)", "",
             "tuning freeze: " + " · ".join(freeze_status(PROJECT_ROOT)), "",
             "| k | floor | context recall | all gold in context | mean sources | right refusals | wrong refusals |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        mark = " ← chosen" if r is best else (" ← naive default" if r is naive else "")
        lines.append(f"| {r['k']} | {r['floor']} | {r['context_recall']:.1%} | {r['all_in_context']:.1%} | "
                     f"{r['mean_sources']:.1f} | {len(r['right_refusals'])} | {len(r['wrong_refusals'])}{mark} |")
    lines += ["", f"chosen: k={best['k']}, floor={best['floor']} · right refusals {best['right_refusals']} · "
              f"wrong refusals {best['wrong_refusals']}",
              f"naive (k=8, floor=0): right refusals {naive['right_refusals']} · wrong refusals {naive['wrong_refusals']}"]
    report = "\n".join(lines) + "\n"
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.md").write_text(report, encoding="utf-8")
    (args.out / "sweep.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
