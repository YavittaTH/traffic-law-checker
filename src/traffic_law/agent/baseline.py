"""LLM-only baseline: one call, the offense catalogue in the prompt, no statute text, no tools,
no grounding. Same output schema as the agent, so both are scored the same way.

It is a strong baseline on purpose: with only ~23 offenses the model can classify from the
list alone. Whatever the agent adds (query rewriting, statute text, grounding, computed
penalties) has to show up as a difference against this.
"""
from __future__ import annotations

import time

from ..llm import chat_json
from ..schemas import PenaltyRule, Verdict

BASELINE_SYSTEM = """You are a Thai traffic-law assistant. Decide which offenses from the catalogue below the DRIVER
committed in the user's story. Answer with ONE JSON object only:
{{"status": "violations_found" | "no_violation" | "need_more_info" | "out_of_scope",
 "violations": [{{"offense_id": "<id from the catalogue>", "reason": "<Thai>", "citation_key": ""}}],
 "follow_up_question": null or "<one Thai question>",
 "summary_th": "<Thai>"}}
Negation matters ("ใส่หมวกแล้ว" = no helmet offense). Use out_of_scope when something is wrong but not in the
catalogue (parking, car tax, never had a licence, headlights). Use need_more_info when a deciding fact is missing.
Read casual Thai the way an ordinary Thai person would and draw the obvious everyday inferences. Informal wording
is not missing information: choose need_more_info only when the story does not tell whether the act happened at all.
Choose an offense only when its description plainly covers what the driver did. If it would take a stretch to fit,
answer out_of_scope instead, and do not add offenses the story does not describe.

Catalogue (offense_id: description):
{catalogue}"""


def run_baseline(story: str, rules: dict[str, PenaltyRule], *, client=None) -> tuple[Verdict, float]:
    t0 = time.time()
    catalogue = "\n".join(f"- {r.offense_id}: {r.description}" for r in rules.values())
    messages = [{"role": "system", "content": BASELINE_SYSTEM.format(catalogue=catalogue)},
                {"role": "user", "content": story}]
    v = chat_json(messages, Verdict, client=client)
    v = v.model_copy(update={"violations": [x for x in v.violations if x.offense_id in rules]})
    if v.status != "violations_found":
        v = v.model_copy(update={"violations": []})
    return v, time.time() - t0
