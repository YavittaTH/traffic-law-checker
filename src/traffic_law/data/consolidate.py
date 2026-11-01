"""Apply an amending act (e.g. ฉบับที่ ๑๓ พ.ศ. ๒๕๖๕) to the sections of the main act.

Each amending section is classified by its instruction (the text before the first quote):

  replace   "ให้ยกเลิกความในมาตรา ๔๓ ... และให้ใช้ความต่อไปนี้แทน"   -> quoted text replaces the section
  insert    "ให้เพิ่มความต่อไปนี้เป็นมาตรา ๑๒๓/๑ มาตรา ๑๒๓/๒ และ..."  -> quoted sections are added
  repeal    "ให้ยกเลิกมาตรา ๑๔๔"                                     -> the section is removed
  partial   "ให้ยกเลิกความในวรรคหนึ่งของมาตรา ๑๔๘", "ให้ยกเลิกอัตราโทษในมาตรา ๑๕๗",
            "ให้เพิ่มความต่อไปนี้เป็นวรรคหกของมาตรา ๑๔๒"
            -> cannot be spliced reliably, so the old text is kept and the amendment is
               APPENDED as a marked note, so retrieval and the LLM always see the current rule.
  other     transitional provisions etc. -> ignored (reported)

A replace whose quoted text has a different number (มาตรา ๑๔ replaces ๑๔๓ ทวิ with “มาตรา ๑๔๓/๑”)
removes the old section and adds the new one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..schemas import Section
from .statute import SID, base_num, norm_sid

# lenient, matched with spaces removed: the gazette PDF garbles it ("แห่งพระราชบัญญัตจิ ราจรทางบก")
# and wraps it mid-word ("...จราจร\nทางบก")
MAIN_ACT_REF = r"แห่งพระราช\S*?ราจรทางบก"


def _refs_main_act(s: str) -> bool:
    return re.search(MAIN_ACT_REF, re.sub(r"\s+", "", s)) is not None
_SID_LIST = re.compile(rf"มาตรา\s*({SID})")
_QUOTED_HEADER = re.compile(rf"^“?\s*มาตรา\s*({SID})(?=\s|$)(?!\s*(?:\.\.\.|…))")
_RATE_LINE = re.compile(rf"^มาตรา\s*({SID})(?:\s*วรรค\S+)?\s*(?:\.\.\.|…)\s*(“.*)$")


@dataclass
class ConsolidationReport:
    replaced: list[str] = field(default_factory=list)
    inserted: list[str] = field(default_factory=list)
    repealed: list[str] = field(default_factory=list)
    partial: list[str] = field(default_factory=list)
    partial_fallback: list[str] = field(default_factory=list)  # could not splice: note appended
    ignored: list[str] = field(default_factory=list)
    missing_targets: list[str] = field(default_factory=list)

    def lines(self) -> list[str]:
        return [f"{k:16} {', '.join(v) if v else '-'}" for k, v in vars(self).items()]


def _instruction(text: str) -> str:
    q = text.find("“")
    head = text if q == -1 else text[:q]
    return re.sub(r"\s+", " ", head)


def _targets(instr: str) -> list[str]:
    """Section ids of the MAIN act named in the instruction (before 'แห่งพระราชบัญญัติ...')."""
    cut = instr.find("แห่งพระราช")
    scope = instr[:cut] if cut != -1 else instr
    scope = re.sub(r"^มาตรา\s*" + SID, "", scope.strip())  # drop the amending section's own header
    return list(dict.fromkeys(norm_sid(x) for x in _SID_LIST.findall(scope)))


def _quoted_sections(text: str, wanted: set[str] | None) -> dict[str, str]:
    """New sections inside the quotes, split at headers (all headers if wanted is None)."""
    start = text.find("“")
    if start == -1:
        return {}
    lines = text[start:].splitlines()
    out: dict[str, list[str]] = {}
    cur: str | None = None
    for ln in lines:
        m = _QUOTED_HEADER.match(ln)
        sid = norm_sid(m.group(1)) if m else None
        if sid and (wanted is None or sid in wanted or cur is None):
            cur = sid
            out[cur] = []
        if cur:
            out[cur].append(ln)
    clean = {}
    for sid, ls in out.items():
        body = "\n".join(ls).strip()
        body = re.sub(r"^“\s*", "", body)
        body = re.sub(r"”\s*$", "", body)
        clean[sid] = body
    return clean


def classify(text: str) -> str:
    instr = _instruction(text)
    if not _refs_main_act(instr) and "“" not in text:
        return "other"
    if re.search(rf"ให้ยกเลิกความในมาตรา\s*{SID}", instr):
        return "replace"
    if re.search(rf"ให้เพิ่มความต่อไปนี้เป็นมาตรา\s*{SID}", instr):
        return "insert"
    if re.search(rf"ให้ยกเลิกมาตรา\s*{SID}", instr):
        return "repeal"
    if re.search(r"ให้(ยกเลิก|เพิ่ม)", instr) and _refs_main_act(instr):
        return "partial"
    return "other"


def consolidate(
    main: list[Section], amending: list[Section]
) -> tuple[list[Section], ConsolidationReport]:
    by_id: dict[str, Section] = {s.section: s for s in main}
    order = [s.section for s in main]
    rep = ConsolidationReport()
    tmpl = main[0]

    def new_section(sid: str, text: str, amend: Section) -> Section:
        return Section(
            doc_id=tmpl.doc_id, act=tmpl.act, unit="มาตรา", section=sid, text=text,
            amended_by=[amend.key], effective_from=amend.effective_from, source=amend.source,
        )

    for am in amending:
        kind = classify(am.text)
        instr = _instruction(am.text)
        targets = _targets(instr)
        tag = f"{am.section}"
        if kind == "other":
            rep.ignored.append(tag)
            continue
        if kind == "repeal":
            for t in targets:
                if by_id.pop(t, None) is not None:
                    rep.repealed.append(t)
                else:
                    rep.missing_targets.append(t)
            continue
        if kind in ("replace", "insert"):
            quoted = _quoted_sections(am.text, set(targets))
            if kind == "replace":
                for t in targets:
                    if t not in by_id:
                        rep.missing_targets.append(t)
                    elif t not in quoted:  # renumbered: old one goes away
                        by_id.pop(t)
                        rep.repealed.append(t)
            for sid, body in quoted.items():
                if sid in by_id:
                    rep.replaced.append(sid)
                else:
                    order.append(sid)
                    rep.inserted.append(sid)
                prev = by_id.get(sid)
                by_id[sid] = new_section(sid, body, am).model_copy(update={
                    "previous_text": (prev.previous_text or prev.text) if prev else None,
                    "amended_by": (prev.amended_by if prev else []) + [am.key],
                })
            continue
        # partial: splice into the right paragraph; if that is not possible, append a note
        rates = _rate_changes(am.text)
        para = _paragraph_target(instr)
        quoted = _quoted_body(am.text)
        for t in targets:
            if t not in by_id:
                rep.missing_targets.append(t)
                continue
            s = by_id[t]
            new_text = None
            if t in rates:
                idx, phrase = rates[t]
                new_text = _replace_rate(s.text, idx, phrase)
            elif para and quoted:
                action, idx = para
                new_text = _splice_paragraph(s.text, action, idx, quoted)
            if new_text is None:
                new_text = f"{s.text}\n\n[แก้ไขโดย {am.act} มาตรา {am.section}]: {rates.get(t, (0, am.text))[1]}"
                rep.partial_fallback.append(t)
            else:
                rep.partial.append(t)
            by_id[t] = s.model_copy(update={
                "text": new_text,
                "amended_by": s.amended_by + [am.key],
                "previous_text": s.previous_text if s.previous_text is not None else s.text,
            })

    def sort_key(sid: str) -> tuple:
        return (base_num(sid), order.index(sid))

    final = [by_id[k] for k in sorted({k for k in order if k in by_id}, key=sort_key)]
    return final, rep


# ------------------------------------------------------------ splicing partial amendments
_ORDINAL = {"หนึ่ง": 0, "สอง": 1, "สาม": 2, "สี่": 3, "ห้า": 4, "หก": 5, "เจ็ด": 6, "แปด": 7, "เก้า": 8, "สิบ": 9}
# the punishment clause of a paragraph: "ต้องระวางโทษ[จำคุก... หรือ]ปรับ(ไม่เกินX บาท|ตั้งแต่X บาทถึงY บาท)[หรือทั้งจำทั้งปรับ]"
_PENALTY = re.compile(
    r"ต้องระวางโทษ\s*(?:จำคุก[\s\S]{0,60}?หรือ\s*)?ปรับ\s*"
    r"(?:ไม่เกิน\s*\S+?บาท|ตั้งแต่\s*\S+?บาท\s*ถึง\s*\S+?บาท)(?:\s*หรือ\s*ทั้งจำทั้งปรับ)?"
)
_RATE = re.compile(rf"มาตรา\s*({SID})(?:\s*วรรค(\S+?))?\s*(?:\.\.\.|…)\s*“([^”]*)”")


def _rate_changes(text: str) -> dict[str, tuple[int, str]]:
    """'มาตรา ๑๕๗/๑ วรรคหนึ่ง ... “ต้องระวางโทษ...”' -> {'157/1': (0, 'ต้องระวางโทษ...')}"""
    flat = re.sub(r"\s+", " ", text)
    return {norm_sid(m.group(1)): (_ORDINAL.get(m.group(2) or "หนึ่ง", 0), m.group(3).strip())
            for m in _RATE.finditer(flat)}


def _paragraph_target(instr: str) -> tuple[str, int] | None:
    """('replace'|'add', paragraph index) from 'ยกเลิกความในวรรคห้าของมาตรา...' / 'เพิ่มความต่อไปนี้เป็นวรรคหกของมาตรา...'."""
    m = re.search(r"(ยกเลิกความใน|เพิ่มความต่อไปนี้เป็น)วรรค(\S+?)ของมาตรา", instr)
    if not m or m.group(2) not in _ORDINAL:
        return None
    return ("replace" if m.group(1).startswith("ยกเลิก") else "add"), _ORDINAL[m.group(2)]


def _quoted_body(text: str) -> str | None:
    a, b = text.find("“"), text.rfind("”")
    return text[a + 1 : b].strip() if a != -1 and b > a else None


_CLAUSE_START = re.compile(r"^\((?:[๐-๙0-9]+|[ก-ฮ])\)")


def _paragraphs(text: str) -> list[str]:
    """Legal paragraphs (วรรค). Indented sub-clauses "(๑) ...", "(ก) ..." belong to the
    paragraph before them, so they are joined back instead of counted as a new วรรค."""
    out: list[str] = []
    for block in (b.strip() for b in text.split("\n\n")):
        if not block:
            continue
        if out and _CLAUSE_START.match(block):
            out[-1] += "\n" + block
        else:
            out.append(block)
    return out


def _replace_rate(text: str, idx: int, phrase: str) -> str | None:
    paras = _paragraphs(text)
    if idx >= len(paras):
        return None
    hits = list(_PENALTY.finditer(paras[idx]))
    if len(hits) != 1:          # none, or ambiguous: do not guess
        return None
    h = hits[0]
    paras[idx] = paras[idx][: h.start()] + phrase + paras[idx][h.end():]
    return "\n\n".join(paras)


def _splice_paragraph(text: str, action: str, idx: int, new: str) -> str | None:
    paras = _paragraphs(text)
    if action == "replace" and idx < len(paras):
        paras[idx] = new
    elif action == "add" and idx == len(paras):
        paras.append(new)
    else:                       # paragraph count does not match the instruction
        return None
    return "\n\n".join(paras)
