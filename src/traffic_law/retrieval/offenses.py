"""Offense catalogue retrieval: one small document per row of data/penalties.csv.

Statute sections alone are a poor target for some offenses: "not stopping at a zebra
crossing" is punished under มาตรา ๒๑, whose text only says "obey traffic signals and signs".
The point regulation (ข้อ ๑๑) describes every offense in plain words, so each catalogue
document joins
  * the table's description,
  * the regulation item text, e.g. ข้อ 11.1(1) "ขับรถไม่หยุดให้คนเดินข้ามทาง ณ ทางข้าม ...",
  * the defining clause of the statute, e.g. มาตรา ๔๓ (๗) "บนทางเท้าโดยไม่มีเหตุอันสมควร".
Searching it returns candidate offenses directly, which is what the agent needs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..data.consolidate import _paragraphs
from ..schemas import PenaltyRule, Section
from ..thai_text import thai_to_arabic

REG_DOC = "point-system-reg-2565"
_THAI = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")


def regulation_items(sections: list[Section]) -> dict[str, str]:
    """ข้อ ๑๑ of the point regulation -> {'11.1(1)': 'ขับรถไม่หยุดให้คนเดินข้ามทาง ...', ...}."""
    reg = next((s for s in sections if s.doc_id == REG_DOC and s.section == "11"), None)
    if reg is None:
        return {}
    text = reg.text.split("\nให้ตัดคะแนนความประพฤติในการขับรถตามจำนวน")[0]
    out: dict[str, str] = {}
    for block in re.split(r"(?m)^(?=[๐-๙]+\.[๐-๙]+\s)", text):
        m = re.match(r"([๐-๙]+\.[๐-๙]+)", block)
        if not m:
            continue
        sub = thai_to_arabic(m.group(1))
        for item in re.finditer(r"(?ms)^\(([๐-๙]+)\)(.*?)(?=^\([๐-๙]+\)|\Z)", block):
            out[f"{sub}({thai_to_arabic(item.group(1))})"] = re.sub(r"\s+", " ", item.group(2)).strip()
    return out


def clause_text(section: Section | None, clause: str) -> str:
    """The sub-clause '(๗)' of a section if named, else its first paragraph (trimmed)."""
    if section is None:
        return ""
    paras = _paragraphs(section.text)
    if clause.startswith("("):
        m = re.search(rf"(?m)^{re.escape(clause)}(.*)$", section.text)
        if m:
            return m.group(1).strip()
    return re.sub(r"\s+", " ", paras[0] if paras else section.text)[:300]


@dataclass(frozen=True)
class OffenseDoc:
    offense_id: str
    text: str


def build_offense_docs(rules: dict[str, PenaltyRule], sections: list[Section]) -> list[OffenseDoc]:
    by_key = {s.key: s for s in sections}
    items = regulation_items(sections)
    docs = []
    for r in rules.values():
        ref = re.search(r"ข้อ (\d+\.\d+\(\d+\))", r.source)
        item = items.get(ref.group(1), "") if ref else ""
        item = re.sub(r"\(มาตรา.*?\)\s*$", "", item)        # drop the trailing "(มาตรา ... )" citation
        sec = by_key.get(f"{r.law}:{r.section}")
        docs.append(OffenseDoc(r.offense_id, " ".join(x for x in (r.description, item, clause_text(sec, r.clause)) if x)))
    return docs
