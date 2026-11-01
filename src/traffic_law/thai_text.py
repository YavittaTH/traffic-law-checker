"""Thai text helpers: digits and repairs for text extracted from government PDFs.

Defects seen in the real files (see tests/test_thai_text.py):
  Royal Gazette (ราชกิจจานุเบกษา)
    * SARA AM split into a space + SARA AA:        "ก าหนด"   -> "กำหนด"
    * tone mark typed before an upper vowel:         "เพ่ิม"    -> "เพิ่ม"
    * a stray space before a combining mark:         "ให้ไว ้"   -> "ให้ไว้"
    * running header lines:                          "หน้า ๕", "เล่ม ๑๓๙ ตอนที่ ... ราชกิจจานุเบกษา ..."
  Council of State (krisdika) consolidated acts
    * the font maps SARA AA to SARA AM, and a real SARA AM comes out as " ำ":
        "ส ำนักงำน" -> "สำนักงาน",  "มำตรำ" -> "มาตรา"
    * page header "- ๒ - สำนักงานคณะกรรมการกฤษฎีกา" and footnote stars "จราจร*"
    (the grey diagonal watermark is removed at extraction time, see scripts/build_corpus.py)
"""
from __future__ import annotations

import re
import unicodedata

_THAI_DIGITS = "๐๑๒๓๔๕๖๗๘๙"
_TO_ARABIC = str.maketrans(_THAI_DIGITS, "0123456789")

_CONS = "ก-ฮ"
_TONE = "่-๋"                   # ่ ้ ๊ ๋
_UPPER_VOWEL = "ัิ-ื"       # ั ิ ี ึ ื
_COMBINING = "ัิ-ฺ็-๎"

_SPLIT_AM = re.compile(rf"([{_CONS}][{_TONE}]?)\s+า")
_TONE_BEFORE_VOWEL = re.compile(rf"([{_TONE}])([{_UPPER_VOWEL}])")
_SPACE_BEFORE_MARK = re.compile(rf"(?<=[{_CONS}{_COMBINING}])\s+(?=[{_COMBINING}])")
_SPACES = re.compile(r"[ \t ​]+")

_HEADER_LINES = [
    re.compile(r"^หน้า\s*[๐-๙0-9]+$"),
    re.compile(r"^เล่ม\s*[๐-๙0-9]+.*ราชกิจจานุเบกษา.*$"),
    re.compile(r"^-\s*[๐-๙0-9]+\s*-$"),
]
_KRISDIKA_HEADER = re.compile(r"(-\s*[๐-๙0-9]+\s*-\s*)?สำนักงานคณะกรรมการกฤษฎีกา")
_FOOTNOTE_STAR = re.compile(r"(?<=[฀-๿\)])\*+")
# krisdika editorial notes: [คำว่า “...” แก้ไขเพิ่มเติมโดยมาตรา ๔ แห่ง ... (ฉบับที่ ๑๑) พ.ศ. ๒๕๕๙]
_EDITOR_NOTE = re.compile(r"\[[^\[\]]{0,600}?(?:แก้ไขเพิ่มเติมโดย|เพิ่มโดย|ยกเลิกโดย)[^\[\]]{0,600}\]")


def thai_to_arabic(text: str) -> str:
    """'มาตรา ๑๒๒/๑' -> 'มาตรา 122/1'."""
    return text.translate(_TO_ARABIC)


def fix_aa_as_am(text: str) -> str:
    """Undo the krisdika font mapping (า shown as ำ, ำ shown as ' ำ').

    Applied only when the text has (almost) no SARA AA at all, so normal text is untouched.
    """
    n_aa, n_am = text.count("า"), text.count("ำ")
    # real Thai has far more า than ำ; 20+ ำ with (almost) no า only happens with this font,
    # and 20 (not 100) lets a single short page, e.g. laws_03.pdf p.31, be fixed on its own
    if n_am < 20 or n_aa > n_am * 0.05:
        return text
    text = re.sub(r"\s+ำ", "\x00", text)
    return text.replace("ำ", "า").replace("\x00", "ำ")


def normalize_pdf_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = fix_aa_as_am(text)
    text = _SPLIT_AM.sub(lambda m: m.group(1) + "ำ", text)
    text = _TONE_BEFORE_VOWEL.sub(r"\2\1", text)
    text = _SPACE_BEFORE_MARK.sub("", text)
    text = _KRISDIKA_HEADER.sub("", text)
    text = _FOOTNOTE_STAR.sub("", text)
    text = _EDITOR_NOTE.sub("", text)
    out = []
    for ln in text.splitlines():
        ln = _SPACES.sub(" ", ln).strip()
        if any(p.match(ln) for p in _HEADER_LINES):
            continue
        out.append(ln)
    return "\n".join(out)
