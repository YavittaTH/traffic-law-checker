"""Grounding: the final answer may only use what the tools actually returned.

* every offense_id must be in the penalty table AND have been returned by a tool;
* its citation must be a section key a tool returned (else the offense's own defining
  section is used when that was returned, so a slightly wrong citation is repaired, not
  dropped);
* a status other than violations_found carries no violations;
* "violations_found" with nothing left after the checks becomes "need_more_info".
Penalties are then computed by code from the surviving offense ids, never by the model.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..data.penalties import summarize
from ..schemas import PenaltyRule, PenaltySummary, Verdict, Violation
from .tools import Seen

FALLBACK_QUESTION = "ช่วยเล่ารายละเอียดเพิ่มอีกนิดได้ไหมครับ เช่น ขับรถอะไร ทำอะไร และเกิดอะไรขึ้น"


@dataclass
class Grounded:
    verdict: Verdict
    penalty: PenaltySummary | None
    notes: list[str] = field(default_factory=list)


def ground(verdict: Verdict, seen: Seen, rules: dict[str, PenaltyRule]) -> Grounded:
    notes: list[str] = []
    if verdict.status != "violations_found":
        if verdict.violations:
            notes.append(f"status {verdict.status}: dropped {len(verdict.violations)} listed violation(s)")
        v = verdict.model_copy(update={"violations": []})
        if v.status == "need_more_info" and not v.follow_up_question:
            v = v.model_copy(update={"follow_up_question": FALLBACK_QUESTION})
        return Grounded(v, None, notes)

    kept: list[Violation] = []
    for viol in verdict.violations:
        oid = viol.offense_id
        if oid not in rules:
            notes.append(f"dropped {oid}: not in the penalty table")
            continue
        if oid not in seen.offenses:
            notes.append(f"dropped {oid}: no tool returned it")
            continue
        if any(k.offense_id == oid for k in kept):
            continue
        own = f"{rules[oid].law}:{rules[oid].section}"
        cite = viol.citation_key
        if cite not in seen.sections:
            if own in seen.sections:
                notes.append(f"{oid}: citation {cite!r} not returned by a tool -> {own}")
                cite = own
            elif rules[oid].law != "land-traffic-2522":
                cite = own          # motor-vehicle act: no text in the corpus, cite by reference
            else:
                notes.append(f"dropped {oid}: no supporting section was returned")
                continue
        kept.append(viol.model_copy(update={"citation_key": cite}))

    if not kept:
        notes.append("no grounded violation left -> need_more_info")
        v = verdict.model_copy(update={"status": "need_more_info", "violations": [],
                                       "follow_up_question": verdict.follow_up_question or FALLBACK_QUESTION})
        return Grounded(v, None, notes)
    v = verdict.model_copy(update={"violations": kept})
    return Grounded(v, summarize([k.offense_id for k in kept], rules), notes)
