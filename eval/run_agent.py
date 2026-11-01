"""End-to-end evaluation: the agent vs the LLM-only baseline on a gold set.

    python eval/run_agent.py                         # main set, both systems
    python eval/run_agent.py --mode agent --limit 5  # quick try
    python eval/run_agent.py --gold eval/heldout.jsonl --out eval/results_agent_heldout --final
    python eval/run_agent.py --mode rag --out eval/results_rag     # classic RAG (rag.py) on the main set

Scores (per system):
  status accuracy    -- right status (violations_found / no_violation / need_more_info / out_of_scope)
  offense P / R / F1 -- micro-averaged over all rows; any offense predicted on a row whose gold
                        list is empty counts as a false positive
  exact match        -- right status AND exactly the right offense set
  by tag             -- exact match per difficulty tag (no_keyword, typo, negation, multi, ...)
The held-out set needs --final and leaves a stamp file: it is meant to be run once, at the end.
Classic RAG was added AFTER the held-out run (E4), so running it on held-out also needs
--posthoc, and the report is labelled POST-HOC: it is not a clean held-out number.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traffic_law.agent.baseline import run_baseline  # noqa: E402
from traffic_law.agent.loop import run_agent  # noqa: E402
from traffic_law.config import EVAL_DIR, PROJECT_ROOT, get_settings  # noqa: E402
from traffic_law.evaluation import bootstrap_ci, freeze_status, load_gold  # noqa: E402
from traffic_law.rag import answer as run_rag  # noqa: E402
from traffic_law.retrieval.retriever import load_retriever  # noqa: E402


def score(rows: list[dict]) -> dict:
    tp = fp = fn = 0
    status_ok = exact = 0
    for r in rows:
        exp, got = set(r["expected"]), set(r["pred_offenses"])
        tp += len(exp & got); fp += len(got - exp); fn += len(exp - got)
        status_ok += r["pred_status"] == r["status"]
        exact += r["exact"]
    p = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * rc / (p + rc) if p + rc else 0.0
    lo, hi = bootstrap_ci([float(r["exact"]) for r in rows])
    n = len(rows)
    return {"n": n, "status_acc": status_ok / n, "precision": p, "recall": rc, "f1": f1,
            "exact": exact / n, "exact_ci": (lo, hi)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=Path, default=EVAL_DIR / "scenarios.jsonl")
    ap.add_argument("--out", type=Path, default=EVAL_DIR / "results_agent")
    ap.add_argument("--mode", choices=["agent", "baseline", "rag", "both", "all"], default="both")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--final", action="store_true", help="required for the held-out set")
    ap.add_argument("--posthoc", action="store_true",
                    help="allow systems built after the held-out run (rag) on held-out; labels the report")
    args = ap.parse_args()

    systems = {"both": ["agent", "baseline"], "all": ["agent", "rag", "baseline"]}.get(args.mode, [args.mode])
    heldout = "heldout" in args.gold.name
    if heldout and not args.final:
        raise SystemExit("held-out is run once, at the end: add --final when you are done changing the system")
    if heldout and "rag" in systems and not args.posthoc:
        raise SystemExit("classic RAG was built after the held-out run: add --posthoc (the report is labelled)")
    if heldout and (args.out / "RAN_ONCE.txt").exists():
        raise SystemExit(f"{args.out} already holds the one held-out run: choose another --out")

    gold = load_gold(args.gold)[: args.limit or None]
    retriever = load_retriever(with_dense=False)
    results: dict[str, list[dict]] = {s: [] for s in systems}
    tool_use: Counter = Counter()
    grounding_drops = 0

    for i, g in enumerate(gold, 1):
        for s in systems:
            if s == "agent":
                res = run_agent(g["scenario"], retriever)
                v, extra = res.verdict, {"steps": [st.__dict__ for st in res.steps], "notes": res.notes,
                                         "llm_calls": res.llm_calls, "seconds": round(res.seconds, 1),
                                         "penalty": res.penalty.model_dump() if res.penalty else None}
                tool_use.update(st.tool for st in res.steps)
                grounding_drops += sum("dropped" in n for n in res.notes)
            elif s == "rag":
                res = run_rag(g["scenario"], retriever)
                v, extra = res.verdict, {"sources": [x.offense_id for x in res.sources], "refused": res.refused,
                                         "notes": res.notes, "llm_calls": res.llm_calls,
                                         "seconds": round(res.seconds, 1),
                                         "penalty": res.penalty.model_dump() if res.penalty else None,
                                         "gold_in_sources": sorted(set(g["expected"]) &
                                                                   {x.offense_id for x in res.sources})}
            else:
                v, secs = run_baseline(g["scenario"], retriever.rules)
                extra = {"seconds": round(secs, 1)}
            pred = sorted({x.offense_id for x in v.violations})
            row = {**g, "pred_status": v.status, "pred_offenses": pred,
                   "exact": v.status == g["status"] and set(pred) == set(g["expected"]),
                   "summary_th": v.summary_th, "follow_up": v.follow_up_question, **extra}
            results[s].append(row)
            print(f"[{i}/{len(gold)}] {s:8} {g['id']} {'✓' if row['exact'] else '✗'} "
                  f"{v.status} {pred}  (gold {g['status']} {g['expected']})")

    lines = [f"# Agent evaluation — {args.gold.name} ({len(gold)} stories)", "",
             f"model: {get_settings().llm_model} · run at {datetime.now(timezone.utc).isoformat(timespec='minutes')}",
             "", "tuning freeze: " + " · ".join(freeze_status(PROJECT_ROOT)), "",
             *(["**POST-HOC**: classic RAG was built after the held-out results were seen; "
                "this is not a clean held-out number.", ""] if heldout and "rag" in systems else []),
             "| system | status acc | offense P | offense R | offense F1 | exact match | exact 95% CI |",
             "|---|---|---|---|---|---|---|"]
    for s in systems:
        m = score(results[s])
        lines.append(f"| {s} | {m['status_acc']:.1%} | {m['precision']:.1%} | {m['recall']:.1%} | "
                     f"{m['f1']:.1%} | {m['exact']:.1%} | {m['exact_ci'][0]:.0%}–{m['exact_ci'][1]:.0%} |")
    tags = sorted({t for g in gold for t in g.get("tags", [])})
    lines += ["", "## Exact match by tag", "", "| tag | n | " + " | ".join(systems) + " |",
              "|---|---|" + "---|" * len(systems)]
    for t in tags:
        per = [[r for r in results[s] if t in r.get("tags", [])] for s in systems]
        lines.append(f"| {t} | {len(per[0])} | " + " | ".join(f"{sum(r['exact'] for r in rs) / len(rs):.0%}" for rs in per) + " |")
    if "agent" in systems:
        ar = results["agent"]
        lines += ["", "## Agent behaviour", "",
                  f"- tool calls: {dict(tool_use)}",
                  f"- mean LLM calls per story: {sum(r['llm_calls'] for r in ar) / len(ar):.1f} · "
                  f"mean seconds: {sum(r['seconds'] for r in ar) / len(ar):.1f}",
                  f"- answers changed by the grounding check: {sum(1 for r in ar if r['notes'])} "
                  f"(offenses dropped: {grounding_drops})"]
    if "rag" in systems:
        rr = results["rag"]
        n_gold = sum(len(r["expected"]) for r in rr)
        lines += ["", "## Classic RAG behaviour", "",
                  f"- k={get_settings().rag_k}, min_score={get_settings().rag_min_score}",
                  f"- gold offenses that reached the sources: {sum(len(r['gold_in_sources']) for r in rr)}/{n_gold} "
                  "(the model cannot answer an offense it was not shown)",
                  f"- refused (nothing above the floor, no LLM call): {sum(r['refused'] for r in rr)}",
                  f"- mean seconds: {sum(r['seconds'] for r in rr) / len(rr):.1f}",
                  f"- answers changed by the grounding check: {sum(1 for r in rr if r['notes'])}"]
    report = "\n".join(lines) + "\n"

    pq = ["# Per story", ""]
    for g_i, g in enumerate(gold):
        pq.append(f"## {g['id']} — {g['scenario']}")
        pq.append(f"gold: `{g['status']}` {g['expected']}  ")
        for s in systems:
            r = results[s][g_i]
            pq.append(f"- **{s}** {'✓' if r['exact'] else '✗'} `{r['pred_status']}` {r['pred_offenses']}"
                      + (f" — notes: {r['notes']}" if r.get("notes") else ""))
        pq.append("")

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.md").write_text(report, encoding="utf-8")
    (args.out / "per_query.md").write_text("\n".join(pq), encoding="utf-8")
    (args.out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.final:
        (args.out / "RAN_ONCE.txt").write_text(
            f"held-out run at {datetime.now(timezone.utc).isoformat()} — do not re-run after changing the system\n",
            encoding="utf-8")
    print("\n" + report)


if __name__ == "__main__":
    main()
