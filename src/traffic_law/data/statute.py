"""Split the text of a Thai act (or regulation) into one record per มาตรา / ข้อ.

Rules learned from the real PDFs:
  * A header is "มาตรา <id>" at the START of a line, id like ๔๓, ๑๒๒/๑, ๔๓ ทวิ, ๔๓ ทวิ/๑.
    "ให้ยกเลิกความในมาตรา ๓๕ ..." in the middle of a line is a reference, not a header.
  * A cross-reference the PDF wrapped onto a new line ("...ตาม\\nมาตรา ๔๓ (๑) หรือ ...") is
    rejected by a lookahead (sub-clause, วรรค, แห่ง, conjunction, "...") and because section
    numbers never go down inside one act.
  * Amending acts quote the new wording, sometimes several new sections in ONE quote:
        “มาตรา ๑๒๓/๑ ...
        มาตรา ๑๒๓/๒ ...           <- no opening quote, still quoted text
        มาตรา ๑๒๓/๓ ...”
    so for amending acts we track quote depth and never start a header inside a quote.
  * Krisdika consolidated acts append the transitional parts of every amending act after
    the main body; `end_marker` cuts the text there.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from ..schemas import Section
from ..thai_text import normalize_pdf_text, thai_to_arabic

NUM = r"[0-9๐-๙]+"
SUFFIX = r"(?:ทวิ|ตรี|จัตวา|เบญจ)"
# raw section id as written: ๑๒๒/๑ | ๔๓ ทวิ | ๔๓ ทวิ/๑ | ๑๖๐ ตรี/๓
SID = rf"{NUM}(?:/{NUM})?(?:\s*{SUFFIX})?(?:/{NUM})?"

# also forbid a following suffix or "/": otherwise backtracking turns "๑๖๐ ตรี/๓ แห่ง..." into "๑๖๐"
_NOT_HEADER = (
    rf"(?!\s*(?:\(|วรรค|แห่ง|และ|หรือ|ถึง|ประกอบ|\.\.\.|…|ของ|{SUFFIX}|/))"
)


def _header_re(unit: str) -> re.Pattern[str]:
    return re.compile(rf"^{unit}\s*({SID})(?=\s|$){_NOT_HEADER}")


def norm_sid(raw: str) -> str:
    """'๔๓ ทวิ/๑' -> '43ทวิ/1'."""
    return re.sub(r"\s+", "", thai_to_arabic(raw))


def base_num(section_id: str) -> int:
    return int(re.match(r"\d+", section_id).group())


def quote_delta(line: str) -> int:
    return line.count("“") - line.count("”")


def split_sections(
    text: str,
    *,
    doc_id: str,
    act: str,
    unit: str = "มาตรา",
    effective_from: str | None = None,
    source: str = "",
    amending: bool = False,
    end_marker: str | None = None,
    normalized: bool = False,
) -> list[Section]:
    if not normalized:
        text = normalize_pdf_text(text)
    if end_marker:
        m = re.search(end_marker, text, flags=re.MULTILINE)
        if m:
            text = text[: m.start()]
    header = _header_re(unit)
    repealed = re.compile(rf"^{unit}\s*({SID})\s*\(ยกเลิก\)\s*$")  # "มาตรา ๑๖๑ (ยกเลิก)"

    out: list[Section] = []
    cur_id: str | None = None
    last_base = 0
    buf: list[str] = []
    depth = 0

    def flush() -> None:
        # blank lines inside a section mark paragraph (วรรค) breaks: keep one, drop runs
        body = re.sub(r"\n\s*\n+", "\n\n", "\n".join(buf)).strip()
        if cur_id is not None and body:
            out.append(Section(doc_id=doc_id, act=act, unit=unit, section=cur_id, text=body,
                               effective_from=effective_from, source=source))

    for line in text.splitlines():
        if not line:
            if cur_id is not None and buf and buf[-1] != "":
                buf.append("")
            continue
        r = repealed.match(line) if depth == 0 else None
        if r and base_num(norm_sid(r.group(1))) >= last_base:
            flush()
            cur_id, buf, last_base = None, [], base_num(norm_sid(r.group(1)))
            continue
        h = header.match(line) if depth == 0 else None
        if h and base_num(norm_sid(h.group(1))) < last_base:
            h = None  # numbers never go down inside one act: a wrapped cross-reference
        if h:
            flush()
            cur_id, buf = norm_sid(h.group(1)), [line]
            last_base = base_num(cur_id)
        elif cur_id is not None:
            buf.append(line)
        if amending:
            depth = max(depth + quote_delta(line), 0)
    flush()
    return _dedupe(out)


def _dedupe(sections: Iterable[Section]) -> list[Section]:
    """A repeated header line (page break) can split one section; keep the longest text."""
    best: dict[str, Section] = {}
    for s in sections:
        if s.section not in best or len(s.text) > len(best[s.section].text):
            best[s.section] = s
    seen: list[str] = []
    for s in sections:
        if s.section not in seen:
            seen.append(s.section)
    return [best[k] for k in seen]
