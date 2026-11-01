"""The agent: native tool calling, a step budget, guards, then grounding.

    result = run_agent("ขี่มอไซค์ไม่ใส่หมวกแล้วฝ่าไฟแดง", retriever)
    result.verdict, result.penalty, result.steps

Stop conditions
  * final answer   -- the model replies without tool calls; parsed into `Verdict`
                      (JSON repair loop in llm.chat_json if needed)
  * must-search    -- a final answer before any search_offenses call is sent back once
  * no-progress    -- the same tool with the same arguments twice is refused
  * step budget    -- after AGENT_MAX_STEPS tool turns the model must answer without tools
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from ..config import get_settings
from ..llm import chat, chat_json, extract_json
from ..retrieval.retriever import Retriever
from ..schemas import PenaltySummary, Verdict
from .grounding import ground
from .tools import SCHEMAS, Toolbox

SYSTEM = """You are a Thai traffic-law assistant. A user describes something that happened on the road,
usually in casual Thai. Decide which traffic offenses (from the demerit-point catalogue) the DRIVER committed.

How to work:
1. Read the story and list each distinct act of the driver. Rewrite each act in formal Thai legal wording
   before searching, e.g. "เป่าแล้วเกิน" -> "ขับรถในขณะเมาสุรา", "ขึ้นฟุตบาท" -> "ขับรถบนทางเท้า",
   "ขับ 140 ป้าย 90" -> "ขับรถเร็วเกินอัตราที่กำหนด", "ไม่หลบรถพยาบาล" -> "ไม่หลีกทางให้รถฉุกเฉิน".
2. Call search_offenses once per distinct act. Use search_law or get_section only when you need the statute text.
3. Answer with ONE JSON object and nothing else.

Rules:
- Use only offense_id values that search_offenses returned. Cite a section key a tool returned.
- Negation matters: "ใส่หมวกแล้ว", "ไม่ได้ดื่มเลย", "คุยผ่านหูฟังไม่ได้ถือ" mean that offense did NOT happen.
- Read casual Thai the way an ordinary Thai person would and draw the obvious everyday inferences.
  Informal wording is not missing information: choose "need_more_info" only when the story does not
  tell whether the act happened at all.
- Choose an offense only when its statutory wording plainly covers what the driver did. If it would
  take a stretch to fit, answer "out_of_scope" instead, and do not add offenses the story does not describe.
- One act = one offense, even if several facts describe it. A motorcycle rider without a helmet and a
  passenger without a helmet are two offenses (no_helmet, no_helmet_passenger).
- status:
  "violations_found" - at least one catalogue offense clearly happened;
  "no_violation"     - the driver did nothing wrong;
  "need_more_info"   - a fact needed to decide is missing (ask ONE short question in Thai);
  "out_of_scope"     - something may be wrong but it is not in the catalogue (e.g. parking, car tax,
                       driving without ever having a licence, headlights).
- Write reason and summary_th in Thai. Never state fines or points yourself; code computes them.

JSON format:
{"status": "violations_found",
 "violations": [{"offense_id": "red_light", "reason": "เร่งผ่านตอนไฟแดง", "citation_key": "land-traffic-2522:22"}],
 "follow_up_question": null,
 "summary_th": "ฝ่าสัญญาณไฟแดง"}"""

NUDGE_SEARCH = "Before answering, call search_offenses for each act in the story."
NUDGE_ANSWER = "Stop calling tools now. Reply with the final JSON object only."


@dataclass
class Step:
    tool: str
    args: Any
    result: str


@dataclass
class AgentResult:
    verdict: Verdict
    penalty: PenaltySummary | None
    steps: list[Step] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    llm_calls: int = 0
    seconds: float = 0.0

    def to_dict(self) -> dict:
        return {"verdict": self.verdict.model_dump(), "penalty": self.penalty.model_dump() if self.penalty else None,
                "steps": [s.__dict__ for s in self.steps], "notes": self.notes,
                "llm_calls": self.llm_calls, "seconds": round(self.seconds, 2)}


def _assistant_message(msg) -> dict:
    out: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
    if getattr(msg, "tool_calls", None):
        out["tool_calls"] = [{"id": c.id, "type": "function",
                              "function": {"name": c.function.name, "arguments": c.function.arguments or "{}"}}
                             for c in msg.tool_calls]
    return out


def _parse_verdict(text: str | None) -> Verdict | None:
    try:
        return Verdict.model_validate(extract_json(text))
    except (ValueError, ValidationError):
        return None


def run_agent(story: str, retriever: Retriever, *, history: list[dict] | None = None,
              client=None, max_steps: int | None = None, on_step=None) -> AgentResult:
    t0 = time.time()
    max_steps = max_steps or get_settings().agent_max_steps
    tools = Toolbox(retriever)
    messages: list[dict] = [{"role": "system", "content": SYSTEM}, *(history or []),
                            {"role": "user", "content": story}]
    steps: list[Step] = []
    calls_seen: set[str] = set()
    searched = nudged = False
    llm_calls = 0
    verdict: Verdict | None = None

    for _ in range(max_steps):
        msg = chat(messages, tools=SCHEMAS, client=client)
        llm_calls += 1
        if getattr(msg, "tool_calls", None):
            messages.append(_assistant_message(msg))
            for c in msg.tool_calls:
                sig = c.function.name + "|" + json.dumps(_loads(c.function.arguments), sort_keys=True, ensure_ascii=False)
                if sig in calls_seen:
                    result = json.dumps({"error": "repeated call with the same arguments; use the earlier result"})
                else:
                    calls_seen.add(sig)
                    result = tools.call(c.function.name, c.function.arguments or "{}")
                    searched |= c.function.name == "search_offenses"
                step = Step(c.function.name, _loads(c.function.arguments), result)
                steps.append(step)
                if on_step:
                    on_step(step)
                messages.append({"role": "tool", "tool_call_id": c.id, "content": result})
            continue
        if not searched and not nudged:            # answered from memory: make it search once
            nudged = True
            messages += [_assistant_message(msg), {"role": "user", "content": NUDGE_SEARCH}]
            continue
        verdict = _parse_verdict(msg.content)
        if verdict is None:                         # repair loop
            messages += [_assistant_message(msg)]
            verdict = chat_json(messages + [{"role": "user", "content": NUDGE_ANSWER}], Verdict, client=client)
            llm_calls += 1
        break
    if verdict is None:                             # step budget used up
        verdict = chat_json(messages + [{"role": "user", "content": NUDGE_ANSWER}], Verdict, client=client)
        llm_calls += 1

    g = ground(verdict, tools.seen, retriever.rules)
    return AgentResult(g.verdict, g.penalty, steps, g.notes, llm_calls, time.time() - t0)


def _loads(raw) -> Any:
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return raw
