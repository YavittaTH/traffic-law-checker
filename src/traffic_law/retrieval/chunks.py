"""Retrieval units.

A section (มาตรา) is the unit we return and cite, but a few sections are long (มาตรา 4,
the definitions, is ~5,300 characters) -- longer than small embedding models read and long
enough to drown a single relevant paragraph in BM25. So each section is packed into chunks
of whole paragraphs (วรรค) up to `max_chars`; scores are later folded back to the section
by taking its best chunk.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..data.consolidate import _paragraphs
from ..schemas import Section


@dataclass(frozen=True)
class Chunk:
    section_key: str
    idx: int
    text: str             # what is indexed: "มาตรา 43 ..." header + body

    @property
    def key(self) -> str:
        return f"{self.section_key}#{self.idx}"


def make_chunks(sections: list[Section], max_chars: int = 900) -> list[Chunk]:
    out: list[Chunk] = []
    for s in sections:
        head = s.label.split(" พระราชบัญญัติ")[0].split(" ระเบียบ")[0]   # "มาตรา 43 ทวิ"
        pieces: list[str] = []
        for para in _paragraphs(s.text):
            if len(para) <= max_chars:
                pieces.append(para)
                continue
            buf = ""                                  # one huge paragraph: split on lines
            for line in para.splitlines():
                if buf and len(buf) + len(line) + 1 > max_chars:
                    pieces.append(buf)
                    buf = ""
                buf = f"{buf}\n{line}" if buf else line
            if buf:
                pieces.append(buf)
        packed: list[str] = []
        for p in pieces:
            if packed and len(packed[-1]) + len(p) + 2 <= max_chars:
                packed[-1] += "\n\n" + p
            else:
                packed.append(p)
        for i, body in enumerate(packed or [s.text]):
            text = body if i == 0 else f"{head} (ต่อ)\n{body}"
            out.append(Chunk(section_key=s.key, idx=i, text=text))
    return out
