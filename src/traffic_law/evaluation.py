"""Gold-set loading and retrieval metrics.

Gold rows (eval/README.md): {"id", "scenario", "expected": [offense_id, ...], "status", "tags"}.
For retrieval, the relevant sections of a row are the sections that define its expected
offenses (via data/penalties.csv).
"""
from __future__ import annotations

import json
import random
from pathlib import Path


def load_gold(path: Path) -> list[dict]:
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path.name} line {i}: {e}") from e
    return rows


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    return len(set(ranked[:k]) & relevant) / len(relevant) if relevant else 0.0


def all_found_at_k(ranked: list[str], relevant: set[str], k: int) -> bool:
    return bool(relevant) and relevant <= set(ranked[:k])


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    for i, key in enumerate(ranked, start=1):
        if key in relevant:
            return 1 / i
    return 0.0


def bootstrap_ci(values: list[float], n: int = 2000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
    """95% percentile bootstrap interval of the mean (small gold sets: report it)."""
    if not values:
        return (0.0, 0.0)
    rnd = random.Random(seed)
    means = sorted(sum(rnd.choice(values) for _ in values) / len(values) for _ in range(n))
    return means[int(alpha / 2 * n)], means[int((1 - alpha / 2) * n) - 1]


def freeze_status(root: Path) -> list[str]:
    """Compare the files listed in eval/frozen.json with their hashes at freeze time.
    Returns human-readable lines; any 'CHANGED' line must be reported with the results."""
    import hashlib

    spec_path = root / "eval" / "frozen.json"
    if not spec_path.exists():
        return ["not frozen (eval/frozen.json missing)"]
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    out = [f"frozen at {spec['frozen_at']}"]
    for rel, digest in spec["sha256"].items():
        p = root / rel
        # CRLF -> LF first, so a Windows checkout or an Excel save does not look like an edit
        now = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() if p.exists() else None
        out.append(f"{'unchanged' if now == digest else 'CHANGED since freeze'}: {rel}")
    return out
