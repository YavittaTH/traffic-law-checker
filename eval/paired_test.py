"""Paired comparison of the systems on exact-match, from the saved per_query.md files (no LLM).

    python eval/paired_test.py     # -> eval/results_paired/report.md

Every system answered the same stories, so the right test looks at the stories where exactly
one of two systems was right: the exact McNemar test (two-sided binomial on the discordant
pairs). Comparing whether two independent confidence intervals overlap ignores that pairing.
The three comparisons are one family, so p-values are also Holm-adjusted.
"""
from __future__ import annotations

import argparse
import re
from math import comb
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent

STORY = re.compile(r"^## (\S+) ")
ANSWER = re.compile(r"^- \*\*(\w+)\*\* ([✓✗])")


def read_per_query(path: Path) -> dict[str, dict[str, bool]]:
    """{system: {story id: exact match?}} from one per_query.md."""
    out: dict[str, dict[str, bool]] = {}
    story = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if m := STORY.match(line):
            story = m.group(1)
        elif (m := ANSWER.match(line)) and story:
            out.setdefault(m.group(1), {})[story] = m.group(2) == "✓"
    return out


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact p-value for b and c discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def holm(pvalues: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, in the input order."""
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def compare(a: dict[str, bool], b: dict[str, bool]) -> dict:
    if set(a) != set(b):
        raise ValueError(f"different stories: {sorted(set(a) ^ set(b))}")
    only_a = sorted(k for k in a if a[k] and not b[k])
    only_b = sorted(k for k in a if b[k] and not a[k])
    return {"n": len(a), "a": sum(a.values()), "b": sum(b.values()), "only_a": only_a, "only_b": only_b,
            "p": mcnemar_exact(len(only_a), len(only_b))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=EVAL_DIR / "results_paired")
    args = ap.parse_args()

    main_set = read_per_query(EVAL_DIR / "results_agent_e3" / "per_query.md")
    main_set |= read_per_query(EVAL_DIR / "results_rag" / "per_query.md")
    heldout = read_per_query(EVAL_DIR / "results_agent_heldout" / "per_query.md")

    family = [
        ("agent vs baseline", "main + held-out", compare(main_set["agent"] | heldout["agent"],
                                                         main_set["baseline"] | heldout["baseline"])),
        ("agent vs rag", "main", compare(main_set["agent"], main_set["rag"])),
        ("baseline vs rag", "main", compare(main_set["baseline"], main_set["rag"])),
    ]
    adjusted = holm([c["p"] for _, _, c in family])

    lines = ["# Paired test on exact match (exact McNemar, two-sided)", "",
             "Sources: results_agent_e3, results_rag, results_agent_heldout. RAG was not run on held-out.", "",
             "| comparison | set | n | correct A | correct B | only A right | only B right | p | Holm p |",
             "|---|---|---|---|---|---|---|---|---|"]
    for (name, where, c), p_holm in zip(family, adjusted):
        lines.append(f"| {name} | {where} | {c['n']} | {c['a']} | {c['b']} | {len(c['only_a'])} | "
                     f"{len(c['only_b'])} | {c['p']:.4f} | {p_holm:.4f} |")
    lines += ["", "## Discordant stories", ""]
    for name, _, c in family:
        lines.append(f"- **{name}**: only A right {c['only_a']}; only B right {c['only_b']}")

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
