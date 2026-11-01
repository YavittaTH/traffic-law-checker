"""Classic RAG, the way the course demo (kmitl-llm-app-demo, app/rag.py) does it:

    retrieve once with the user's own words -> keep sources above the min_score floor
    -> show them to the model as a NUMBERED list -> the model answers citing [n]

    res = answer("ขี่มอไซค์ไม่ใส่หมวกแล้วฝ่าไฟแดง", retriever)
    res.verdict, res.penalty, res.sources

Differences from the agent (agent/loop.py), on purpose:
  * one retrieval, one LLM call -- no query rewriting, no tool loop;
  * if no source clears the floor the model is not called at all: the answer is a refusal
    ("out_of_scope": nothing in the catalogue matches), the RAG safety rule from the demo;
  * the model cites sources by number; numbers are mapped back to offense ids and statute
    sections by code, so it cannot cite something it was not shown.
The same grounding check and the same code-computed penalties as the agent are applied after.

Sources are offense-catalogue documents (description + point-regulation item + statute
clause), scored with raw BM25 over the story (after the colloquial-term expansion), because
RRF scores are rank-only and cannot carry a floor. The floor was picked on the main set with
eval/run_min_score.py (docs/experiments.md E5).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, ValidationError

from .agent.grounding import ground
from .agent.tools import Seen
from .config import get_settings
from .llm import chat_json, chat_stream, extract_json
from .retrieval.offenses import clause_text, regulation_items
from .retrieval.retriever import Retriever
from .schemas import PenaltySummary, Verdict, Violation

REFUSAL_SUMMARY = ("ไม่พบข้อหาในระบบที่ตรงกับเรื่องนี้ ระบบนี้ครอบคลุมเฉพาะความผิดที่ถูกตัดคะแนนความประพฤติ "
                   "22 ข้อหา (ระเบียบ สตช. พ.ศ. 2565)")

SYSTEM = """You are a Thai traffic-law assistant. The user tells a story in casual Thai. Below the story is a
NUMBERED list of sources: offenses from the demerit-point catalogue that a search found for this story, each with
the regulation wording and the statute clause. Decide which of these offenses the DRIVER committed.

Rules:
- Use ONLY the numbered sources. Cite each offense by its source number. If the act is not among the sources,
  do not invent one: answer "out_of_scope" if something else may be wrong, or "no_violation".
- The search is keyword-based and returns offenses that did NOT happen too. Choose a source only when its wording
  plainly covers what the driver did.
- Negation matters: "ใส่หมวกแล้ว", "ไม่ได้ดื่มเลย", "คุยผ่านหูฟังไม่ได้ถือ" mean that offense did NOT happen.
- Read casual Thai the way an ordinary Thai person would and draw the obvious everyday inferences. Choose
  "need_more_info" only when the story does not tell whether the act happened at all (ask ONE short Thai question).
- Never state fines or points; code computes them. Write reason and summary_th in Thai.

Answer with ONE JSON object and nothing else:
{"status": "violations_found" | "no_violation" | "need_more_info" | "out_of_scope",
 "violations": [{"source": 2, "reason": "<Thai>"}],
 "follow_up_question": null,
 "summary_th": "<Thai>"}"""


REPAIR = "Your reply was not one valid JSON object. Reply again with ONLY the JSON object."


# ------------------------------------------------------------------ data
@dataclass
class Source:
    n: int
    offense_id: str
    description: str
    regulation: str
    statute: str
    section_key: str | None        # None: motor-vehicle act, no text in the corpus
    section_label: str
    score: float

    def as_prompt(self) -> str:
        lines = [f"[{self.n}] {self.description}"]
        if self.regulation:
            lines.append(f"    ระเบียบ: {self.regulation}")
        lines.append(f"    ตัวบท ({self.section_label}): {self.statute}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return dict(self.__dict__)


class RagViolation(BaseModel):
    source: int
    reason: str = ""


class RagAnswer(BaseModel):
    status: str
    violations: list[RagViolation] = Field(default_factory=list)
    follow_up_question: str | None = None
    summary_th: str = ""


@dataclass
class RagResult:
    verdict: Verdict
    penalty: PenaltySummary | None
    sources: list[Source]
    refused: bool = False
    notes: list[str] = field(default_factory=list)
    llm_calls: int = 0
    seconds: float = 0.0

    def to_dict(self) -> dict:
        return {"verdict": self.verdict.model_dump(), "penalty": self.penalty.model_dump() if self.penalty else None,
                "sources": [s.to_dict() for s in self.sources], "refused": self.refused, "notes": self.notes,
                "llm_calls": self.llm_calls, "seconds": round(self.seconds, 2)}


# ------------------------------------------------------------------ retrieve
def _regulation_items(retriever: Retriever) -> dict[str, str]:
    cache = getattr(retriever, "_rag_reg_items", None)
    if cache is None:
        cache = regulation_items(list(retriever.sections.values()))
        retriever._rag_reg_items = cache
    return cache


def retrieve(story: str, retriever: Retriever, *, k: int | None = None,
             min_score: float | None = None) -> list[Source]:
    """Top-k catalogue offenses whose BM25 score is >= min_score (and > 0), numbered from 1."""
    s = get_settings()
    k = s.rag_k if k is None else k
    min_score = s.rag_min_score if min_score is None else min_score
    import re

    items = _regulation_items(retriever)
    out: list[Source] = []
    for rule, score in retriever.score_offenses(story):
        if len(out) >= k or score <= 0 or score < min_score:
            break
        key = f"{rule.law}:{rule.section}"
        sec = retriever.sections.get(key)
        ref = re.search(r"ข้อ (\d+\.\d+\(\d+\))", rule.source)
        reg = re.sub(r"\(มาตรา.*?\)\s*$", "", items.get(ref.group(1), "") if ref else "").strip()
        out.append(Source(
            n=len(out) + 1, offense_id=rule.offense_id, description=rule.description, regulation=reg,
            statute=(clause_text(sec, rule.clause)[:300] if sec is not None
                     else "อยู่ใน พ.ร.บ.รถยนต์ (ไม่มีตัวบทในระบบ)"),
            section_key=key if sec is not None else None,
            section_label=(_with_clause(sec.label, rule.clause) if sec is not None
                           else f"พ.ร.บ.รถยนต์ มาตรา {rule.section}{rule.clause}"),
            score=round(score, 2)))
    return out


def _with_clause(label: str, clause: str) -> str:
    """'มาตรา 22 พระราชบัญญัติ...' + '(๒)' -> 'มาตรา 22 (๒) พระราชบัญญัติ...'."""
    if not clause:
        return label
    head, sep, act = label.partition(" พระราชบัญญัติ")
    return f"{head} {clause}{sep}{act}"


def build_messages(story: str, sources: list[Source]) -> list[dict]:
    context = "\n\n".join(s.as_prompt() for s in sources)
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"เรื่องที่เล่า:\n{story}\n\nแหล่งข้อมูล (sources):\n{context}"}]


# ------------------------------------------------------------------ answer
def _to_verdict(ans: RagAnswer, sources: list[Source], notes: list[str]) -> Verdict:
    by_n = {s.n: s for s in sources}
    viols: list[Violation] = []
    for v in ans.violations:
        src = by_n.get(v.source)
        if src is None:
            notes.append(f"dropped citation [{v.source}]: no such source")
            continue
        viols.append(Violation(offense_id=src.offense_id, reason=v.reason,
                               citation_key=src.section_key or ""))
    status = ans.status if ans.status in ("violations_found", "no_violation", "need_more_info",
                                          "out_of_scope") else "need_more_info"
    return Verdict(status=status, violations=viols, follow_up_question=ans.follow_up_question,
                   summary_th=ans.summary_th)


def _parse(text: str) -> RagAnswer | None:
    try:
        return RagAnswer.model_validate(extract_json(text))
    except (ValueError, ValidationError):
        return None


def answer(story: str, retriever: Retriever, *, k: int | None = None, min_score: float | None = None,
           client=None, on_token=None) -> RagResult:
    """Retrieve -> numbered context -> one cited answer. `on_token(str)` streams the model output."""
    t0 = time.time()
    sources = retrieve(story, retriever, k=k, min_score=min_score)
    if not sources:                                   # nothing clears the floor: refuse, no LLM call
        v = Verdict(status="out_of_scope", summary_th=REFUSAL_SUMMARY)
        return RagResult(v, None, [], refused=True, seconds=time.time() - t0)

    messages = build_messages(story, sources)
    calls = 1
    if on_token is not None:
        text = "".join(_tee(chat_stream(messages, client=client), on_token))
        ans = _parse(text)
        if ans is None:                               # repair, same discipline as llm.chat_json
            ans = chat_json(messages + [{"role": "assistant", "content": text},
                                        {"role": "user", "content": REPAIR}], RagAnswer, client=client)
            calls += 1
    else:
        ans = chat_json(messages, RagAnswer, client=client)

    notes: list[str] = []
    verdict = _to_verdict(ans, sources, notes)
    seen = Seen(offenses={s.offense_id for s in sources}, sections={s.section_key for s in sources if s.section_key})
    g = ground(verdict, seen, retriever.rules)
    return RagResult(g.verdict, g.penalty, sources, notes=notes + g.notes, llm_calls=calls,
                     seconds=time.time() - t0)


def _tee(tokens, on_token):
    for t in tokens:
        on_token(t)
        yield t
