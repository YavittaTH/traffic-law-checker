"""Agent tests with a scripted fake LLM: tool loop, guards, grounding, baseline, scoring."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

from traffic_law.agent.baseline import run_baseline
from traffic_law.agent.grounding import ground
from traffic_law.agent.loop import NUDGE_SEARCH, run_agent
from traffic_law.agent.tools import Seen, Toolbox
from traffic_law.retrieval.retriever import Retriever
from traffic_law.schemas import PenaltyRule, Section, Verdict, Violation

DOC = "land-traffic-2522"


def sec(sid, text):
    return Section(doc_id=DOC, act="พระราชบัญญัติจราจรทางบก พ.ศ. ๒๕๒๒", section=sid, text=text)


SECTIONS = [
    sec("22", "มาตรา ๒๒ ผู้ขับขี่ต้องปฏิบัติตามสัญญาณจราจร\n\n(๒) สัญญาณจราจรไฟสีแดง ให้ผู้ขับขี่หยุดรถ"),
    sec("43", "มาตรา ๔๓ ห้ามมิให้ผู้ขับขี่ขับรถ\n\n(๒) ในขณะเมาสุราหรือของเมาอย่างอื่น\n\n(๗) บนทางเท้าโดยไม่มีเหตุอันสมควร"),
    sec("122", "มาตรา ๑๒๒ ผู้ขับขี่รถจักรยานยนต์ต้องสวมหมวกที่จัดทำขึ้นโดยเฉพาะเพื่อป้องกันอันตราย"),
]


def rule(oid, desc, section, clause, fine, jail, pts):
    return PenaltyRule(offense_id=oid, description=desc, section=section, clause=clause, penalty_section="152",
                       fine_max=fine, jail_max_months=jail, points=pts, source="test", verified=True)


RULES = {r.offense_id: r for r in [
    rule("drunk", "ขับรถขณะเมาสุราหรือของเมาอย่างอื่น", "43", "(๒)", 20000, 12, 4),
    rule("sidewalk", "ขับรถบนทางเท้าโดยไม่มีเหตุอันสมควร", "43", "(๗)", 4000, 0, 1),
    rule("red_light", "ฝ่าสัญญาณไฟแดง", "22", "(๒)", 4000, 0, 2),
    rule("no_helmet", "ขับขี่รถจักรยานยนต์ไม่สวมหมวกนิรภัย", "122", "", 2000, 0, 1),
]}


def retriever():
    return Retriever(SECTIONS, rules=RULES)


# ------------------------------------------------------------------ fake LLM
def tool_msg(*calls):
    return NS(content="", tool_calls=[NS(id=f"c{i}", function=NS(name=n, arguments=json.dumps(a, ensure_ascii=False)))
                                      for i, (n, a) in enumerate(calls)])


def final_msg(obj_or_text):
    text = obj_or_text if isinstance(obj_or_text, str) else json.dumps(obj_or_text, ensure_ascii=False)
    return NS(content=text, tool_calls=None)


class FakeLLM:
    """Returns scripted messages in order and records every request."""

    def __init__(self, *messages):
        self.queue = list(messages)
        self.requests = []
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kw):
        self.requests.append(kw)
        if not self.queue:
            raise AssertionError("FakeLLM ran out of scripted replies")
        return NS(choices=[NS(message=self.queue.pop(0))])


DRUNK_VERDICT = {"status": "violations_found", "summary_th": "เมาแล้วขับ", "follow_up_question": None,
                 "violations": [{"offense_id": "drunk", "reason": "ดื่มแล้วขับ", "citation_key": f"{DOC}:43"}]}


# ------------------------------------------------------------------ loop
def test_happy_path_tool_then_answer_and_code_computed_penalty():
    llm = FakeLLM(tool_msg(("search_offenses", {"query": "ขับรถในขณะเมาสุรา"})), final_msg(DRUNK_VERDICT))
    res = run_agent("ปาร์ตี้มาแล้วขับกลับ", retriever(), client=llm)
    assert res.verdict.status == "violations_found"
    assert [v.offense_id for v in res.verdict.violations] == ["drunk"]
    assert res.penalty.total_fine_max == 20000 and res.penalty.total_points == 4 and res.penalty.any_jail
    assert res.steps[0].tool == "search_offenses" and "drunk" in res.steps[0].result
    assert llm.requests[0]["tools"] and res.llm_calls == 2 and not res.notes


def test_answer_without_searching_is_sent_back_once():
    llm = FakeLLM(final_msg(DRUNK_VERDICT),
                  tool_msg(("search_offenses", {"query": "เมาสุรา"})), final_msg(DRUNK_VERDICT))
    res = run_agent("เมาแล้วขับ", retriever(), client=llm)
    assert any(m.get("content") == NUDGE_SEARCH for m in llm.requests[1]["messages"])
    assert res.verdict.violations[0].offense_id == "drunk"


def test_repeated_identical_call_is_refused():
    same = ("search_offenses", {"query": "เมาสุรา"})
    llm = FakeLLM(tool_msg(same), tool_msg(same), final_msg(DRUNK_VERDICT))
    res = run_agent("เมาแล้วขับ", retriever(), client=llm)
    assert "repeated call" in res.steps[1].result


def test_step_budget_forces_an_answer():
    llm = FakeLLM(tool_msg(("search_offenses", {"query": "a1"})), tool_msg(("search_offenses", {"query": "เมาสุรา"})),
                  final_msg(DRUNK_VERDICT))
    res = run_agent("เมาแล้วขับ", retriever(), client=llm, max_steps=2)
    assert "tools" not in llm.requests[-1] and res.verdict.status == "violations_found"


def test_invalid_final_json_is_repaired():
    llm = FakeLLM(tool_msg(("search_offenses", {"query": "เมาสุรา"})), final_msg("คิดว่าน่าจะผิดเรื่องเมา"),
                  final_msg(DRUNK_VERDICT))
    res = run_agent("เมาแล้วขับ", retriever(), client=llm)
    assert res.verdict.violations[0].offense_id == "drunk" and res.llm_calls == 3


# ------------------------------------------------------------------ grounding
def v(status, *viols, q=None):
    return Verdict(status=status, follow_up_question=q,
                   violations=[Violation(offense_id=o, reason="r", citation_key=c) for o, c in viols])


def test_grounding_drops_unseen_and_unknown_and_repairs_citation():
    seen = Seen(offenses={"drunk", "red_light"}, sections={f"{DOC}:43", f"{DOC}:22"})
    g = ground(v("violations_found", ("drunk", f"{DOC}:999"), ("sidewalk", f"{DOC}:43"), ("made_up", "x:1")),
               seen, RULES)
    assert [x.offense_id for x in g.verdict.violations] == ["drunk"]
    assert g.verdict.violations[0].citation_key == f"{DOC}:43"             # repaired to its own section
    assert any("sidewalk" in n and "no tool returned" in n for n in g.notes)
    assert any("made_up" in n for n in g.notes)
    assert g.penalty.total_fine_max == 20000


def test_grounding_nothing_left_becomes_need_more_info():
    g = ground(v("violations_found", ("sidewalk", f"{DOC}:43")), Seen(), RULES)
    assert g.verdict.status == "need_more_info" and g.verdict.follow_up_question and g.penalty is None


def test_non_violation_status_carries_no_offenses():
    seen = Seen(offenses={"drunk"}, sections={f"{DOC}:43"})
    g = ground(v("no_violation", ("drunk", f"{DOC}:43")), seen, RULES)
    assert g.verdict.violations == [] and g.penalty is None


# ------------------------------------------------------------------ tools
def test_toolbox_validation_and_errors():
    t = Toolbox(retriever())
    assert "unknown tool" in t.call("delete_everything", "{}")
    assert "error" in t.call("search_offenses", '{"query": ""}')
    assert "error" in t.call("get_section", '{"key": "land-traffic-2522:999"}')
    assert "error" in t.call("compute_penalty", '{"offense_ids": ["nope"]}')
    out = json.loads(t.call("compute_penalty", '{"offense_ids": ["drunk", "red_light"]}'))
    assert out["total_points"] == 6 and out["total_fine_max"] == 24000


# ------------------------------------------------------------------ baseline + scoring
def test_baseline_filters_unknown_ids():
    llm = FakeLLM(final_msg({"status": "violations_found", "summary_th": "", "follow_up_question": None,
                             "violations": [{"offense_id": "drunk", "reason": "", "citation_key": ""},
                                            {"offense_id": "invented", "reason": "", "citation_key": ""}]}))
    verdict, _ = run_baseline("เมาแล้วขับ", RULES, client=llm)
    assert [x.offense_id for x in verdict.violations] == ["drunk"]
    assert "drunk: ขับรถขณะเมา" in llm.requests[0]["messages"][0]["content"]   # catalogue in the prompt


def test_score():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
    from run_agent import score

    rows = [
        {"status": "violations_found", "expected": ["a", "b"], "pred_status": "violations_found", "pred_offenses": ["a"], "exact": False},
        {"status": "no_violation", "expected": [], "pred_status": "violations_found", "pred_offenses": ["c"], "exact": False},
        {"status": "violations_found", "expected": ["d"], "pred_status": "violations_found", "pred_offenses": ["d"], "exact": True},
    ]
    m = score(rows)
    assert (round(m["precision"], 3), round(m["recall"], 3)) == (0.667, 0.667)
    assert round(m["status_acc"], 3) == 0.667 and round(m["exact"], 3) == 0.333
