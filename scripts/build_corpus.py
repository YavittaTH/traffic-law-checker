"""Turn the PDFs listed in data/raw/sources.json into data/processed/sections.jsonl.

    python scripts/build_corpus.py                 # build + report
    python scripts/build_corpus.py --show 43       # print the final text of มาตรา 43 (every doc)
    python scripts/build_corpus.py --dump-text     # also write the cleaned full text per source

Source roles in the manifest:
  main        the base act (ideally a consolidated version)
  amendment   an amending act; its changes are applied to the doc named in "amends_doc"
              and its own sections are NOT put in the corpus
  standalone  a separate document (regulation, announcement) indexed as-is; "unit" can be "ข้อ"

The report lists section counts, GAPS in numbering (usually a header the extraction broke --
check those by hand) and what the consolidation did.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traffic_law.config import PROCESSED_DIR, RAW_DIR, SECTIONS_PATH  # noqa: E402
from traffic_law.data.consolidate import consolidate  # noqa: E402
from traffic_law.data.statute import base_num, split_sections  # noqa: E402
from traffic_law.thai_text import normalize_pdf_text  # noqa: E402

BLACK = ((0,), (0.0,), [0], [0.0], (0, 0, 0), (0.0, 0.0, 0.0), None)


PARA_INDENT = 30  # points: a line starting this far right of the page's usual margin opens a วรรค
# "- ๔๒ - สำนักงาน..." (krisdika, raw encoding "ส ำนักงำน"), "หน้า ๕", "เล่ม ๑๓๙ ตอนที่ ... ราชกิจจานุเบกษา ..."
RUNNING_HEADER = re.compile(
    r"^\s*-\s*[๐-๙0-9]+\s*-|^\s*หน้า\s*[๐-๙0-9]+\s*$|^\s*เล่ม\s*[๐-๙0-9]+.*ราชกิจจานุเบกษา"
)


def _page_lines(page) -> list[str]:
    """Lines of one page; an indented line (new paragraph / วรรค) gets a blank line before it."""
    from collections import Counter

    lines = page.extract_text_lines()
    if not lines:
        return []
    # running headers must go here, before they leave a stray paragraph break behind
    lines = [ln for ln in lines if not RUNNING_HEADER.search(ln["text"])]
    if not lines:
        return []
    margin = Counter(round(ln["x0"]) for ln in lines).most_common(1)[0][0]
    out: list[str] = []
    for ln in lines:
        if ln["x0"] - margin >= PARA_INDENT:
            out.append("")
        out.append(ln["text"])
    return out


def extract_pdf(path: Path, *, min_font_size: float = 0.0, black_only: bool = True) -> str:
    """Text of every page; drops grey watermark chars and (optionally) small footnote text.

    Paragraph starts are kept as blank lines, because amendments target paragraphs
    ("ให้ยกเลิกความในวรรคหนึ่งของมาตรา ๑๔๘ ...").
    """
    import pdfplumber

    def keep(obj) -> bool:
        if obj.get("object_type") != "char":
            return True
        if black_only and obj.get("non_stroking_color") not in BLACK:
            return False
        return obj.get("size", 99) >= min_font_size

    with pdfplumber.open(path) as pdf:
        text = "\n".join("\n".join(_page_lines(p.filter(keep))) for p in pdf.pages)
    if len(text.strip()) < 200:
        raise SystemExit(f"{path.name}: almost no text extracted -- scanned PDF? (needs OCR)")
    return text


def gaps(ids: list[str]) -> list[int]:
    nums = sorted({base_num(s) for s in ids})
    return [n for n in range(nums[0], nums[-1] + 1) if n not in set(nums)] if nums else []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=RAW_DIR / "sources.json")
    ap.add_argument("--show", help="print the final text of this section id")
    ap.add_argument("--dump-text", action="store_true")
    args = ap.parse_args()

    if not args.manifest.exists():
        raise SystemExit(f"missing {args.manifest} -- copy sources.example.json and fill it in")
    sources = json.loads(args.manifest.read_text(encoding="utf-8"))

    parsed: dict[str, list] = {}
    meta: dict[str, dict] = {}
    for src in sources:
        raw = extract_pdf(RAW_DIR / src["file"], min_font_size=src.get("min_font_size", 0.0))
        text = normalize_pdf_text(raw)
        if args.dump_text:
            PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
            (PROCESSED_DIR / f"{src['doc_id']}.txt").write_text(text, encoding="utf-8")
        parsed[src["doc_id"]] = split_sections(
            text, normalized=True,
            doc_id=src["doc_id"], act=src["act"], unit=src.get("unit", "มาตรา"),
            effective_from=src.get("effective_from"), source=src.get("url", ""),
            amending=src.get("role") == "amendment", end_marker=src.get("end_marker"),
        )
        meta[src["doc_id"]] = src

    print(f"{'doc_id':26} {'role':10} {'parsed':>6}  gaps")
    for doc_id, secs in parsed.items():
        role = meta[doc_id].get("role", "main")
        g = gaps([s.section for s in secs]) if role != "amendment" else []
        print(f"{doc_id:26} {role:10} {len(secs):>6}  {g[:20] if g else '-'}")

    # apply amendments in manifest order
    for doc_id, src in meta.items():
        if src.get("role") == "amendment":
            target = src["amends_doc"]
            parsed[target], rep = consolidate(parsed[target], parsed[doc_id])
            print(f"\nconsolidation {doc_id} -> {target}")
            for ln in rep.lines():
                print("  " + ln)

    corpus = [s for d, secs in parsed.items() if meta[d].get("role") != "amendment" for s in secs]

    if args.show:
        for s in corpus:
            if s.section == args.show:
                print(f"\n--- {s.label}  (amended_by={s.amended_by}) ---\n{s.text}")
        return

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(SECTIONS_PATH, "w", encoding="utf-8") as f:
        for s in corpus:
            f.write(s.model_dump_json() + "\n")
    print(f"\nwrote {len(corpus)} sections -> {SECTIONS_PATH}")


if __name__ == "__main__":
    main()
