"""Penalty table + the calculator tool.

The LLM decides WHICH offenses apply; this module does all the arithmetic, so totals are
always consistent with the curated table and cannot be hallucinated.

Point rules (ระเบียบ...ระบบการบันทึกคะแนนความประพฤติ พ.ศ. ๒๕๖๕):
  * ข้อ ๗   every licence holder starts with 12 points
  * ข้อ ๑๑  points per offense; several offenses in ONE incident are summed but capped at 8.
            One regulation item counts once: ข้อ 11.1(7) "rider without a helmet OR passenger without
            a helmet" is one item (1 point) even though the table splits it into two rows because
            the fines differ (148 วรรคหนึ่ง vs วรรคสอง).
  * ข้อ ๑๒  reaching 0 points -> licence suspended for 90 days
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from ..config import PENALTIES_PATH, get_settings
from ..schemas import PenaltyRule, PenaltySummary

_OPTIONAL_INT = ("fine_max", "jail_max_months")


class UnknownOffense(KeyError):
    pass


def regulation_item(rule: PenaltyRule) -> str | None:
    """'ข้อ 11.1(7)' style reference in the row's source, used to count an item's points once."""
    m = re.search(r"ข้อ\s*(\d+\.\d+\(\d+\))", rule.source)
    return m.group(1) if m else None


def load_penalties(path: Path = PENALTIES_PATH) -> dict[str, PenaltyRule]:
    rules: dict[str, PenaltyRule] = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            oid = (row.get("offense_id") or "").strip()
            if not oid or oid.startswith("#"):
                continue
            row = {k: (v or "").strip() for k, v in row.items() if k}
            row["verified"] = row.get("verified", "").lower() in {"1", "true", "yes", "y"}
            row["points"] = row.get("points") or "0"
            for k in _OPTIONAL_INT:
                if row.get(k, "") == "":
                    row[k] = None
            if not row.get("law"):
                row.pop("law", None)
            try:
                rule = PenaltyRule.model_validate(row)
            except Exception as e:  # report the CSV line, not just the pydantic error
                raise ValueError(f"{path.name} line {i}: {e}") from e
            if rule.offense_id in rules:
                raise ValueError(f"{path.name} line {i}: duplicate offense_id {rule.offense_id}")
            rules[rule.offense_id] = rule
    return rules


def summarize(
    offense_ids: list[str],
    rules: dict[str, PenaltyRule],
    *,
    points_start: int | None = None,
    incident_cap: int | None = None,
) -> PenaltySummary:
    """Totals for ONE incident. Each offense is counted once even if listed twice."""
    s = get_settings()
    points_start = points_start or s.points_start
    incident_cap = incident_cap or s.points_incident_cap
    ids = list(dict.fromkeys(offense_ids))
    unknown = [o for o in ids if o not in rules]
    if unknown:
        raise UnknownOffense(", ".join(unknown))
    chosen = [rules[o] for o in ids]
    per_item: dict[str, int] = {}
    for r in chosen:                       # one regulation item -> its points once
        item = regulation_item(r) or r.offense_id
        per_item[item] = max(per_item.get(item, 0), r.points)
    raw = sum(per_item.values())
    pts = min(raw, incident_cap)
    left = max(points_start - pts, 0)
    return PenaltySummary(
        offense_ids=ids,
        total_fine_max=sum(r.fine_max for r in chosen if r.fine_max is not None),
        fine_unknown=[r.offense_id for r in chosen if r.fine_max is None],
        points_raw=raw,
        total_points=pts,
        points_capped=raw > incident_cap,
        points_left=left,
        license_suspension_risk=left == 0,
        any_jail=any(r.jail_max_months is None or r.jail_max_months > 0 for r in chosen),
        unverified=[r.offense_id for r in chosen if not r.verified],
    )


def offense_section_keys(offense_ids: list[str], rules: dict[str, PenaltyRule]) -> set[str]:
    """Corpus keys ('land-traffic-2522:43') of the sections that define these offenses.
    Offenses in acts that are not in the corpus (motor-vehicle-2522) are left out."""
    return {f"{rules[o].law}:{rules[o].section}" for o in offense_ids
            if o in rules and rules[o].law == "land-traffic-2522"}


def offenses_for_sections(section_keys: list[str], rules: dict[str, PenaltyRule]) -> list[PenaltyRule]:
    """Penalty rows whose defining section is among `section_keys` (retrieval -> candidate offenses)."""
    keys = set(section_keys)
    return [r for r in rules.values() if f"{r.law}:{r.section}" in keys]
