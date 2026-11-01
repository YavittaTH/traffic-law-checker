"""Thai tokenizer for BM25: pythainlp newmm, Thai digits -> Arabic, stopwords dropped.

pythainlp's stopword list contains a few words that matter in traffic law ("ทาง" as in
ทางเดินรถ, "เกิน" as in ความเร็วเกิน), so those are kept.
"""
from __future__ import annotations

import re
from functools import lru_cache

from ..thai_text import thai_to_arabic

_KEEP = {"ทาง", "เกิน"}
_WORDLIKE = re.compile(r"[ก-ฮ0-9a-z]")


@lru_cache(maxsize=1)
def _stopwords() -> frozenset[str]:
    from pythainlp.corpus import thai_stopwords

    return frozenset(thai_stopwords()) - _KEEP


def tokenize(text: str) -> list[str]:
    from pythainlp.tokenize import word_tokenize

    text = thai_to_arabic(text.lower())
    stop = _stopwords()
    return [t for t in word_tokenize(text, engine="newmm", keep_whitespace=False)
            if _WORDLIKE.search(t) and t not in stop]
