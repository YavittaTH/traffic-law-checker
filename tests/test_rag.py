"""Classic RAG and the web app, with a scripted fake LLM (no network)."""
import json
from types import SimpleNamespace as NS

from fastapi.testclient import TestClient

from traffic_law.api import app as webapp
from traffic_law.rag import REFUSAL_SUMMARY, answer, build_messages, retrieve

from .test_agent import FakeLLM, final_msg, retriever

STORY = "ขี่มอไซค์ไม่ใส่หมวกแล้วฝ่าไฟแดง"


def rag_reply(*cites, status="violations_found"):
    return final_msg({"status": status, "summary_th": "สรุป", "follow_up_question": None,
                      "violations": [{"source": n, "reason": "เหตุผล"} for n in cites]})


class StreamingFakeLLM(FakeLLM):
    """Streams the next scripted reply in small pieces when stream=True."""

    def _create(self, **kw):
        if not kw.get("stream"):
            return super()._create(**kw)
        self.requests.append(kw)
        text = self.queue.pop(0).content
        return iter([NS(choices=[NS(delta=NS(content=text[i:i + 7]))]) for i in range(0, len(text), 7)])


# ------------------------------------------------------------------ retrieve
def test_sources_are_numbered_scored_and_floored():
    r = retriever()
    src = retrieve(STORY, r, k=8, min_score=0.0)
    assert [s.n for s in src] == list(range(1, len(src) + 1))
    assert {"red_light", "no_helmet"} <= {s.offense_id for s in src}
    assert all(s.score > 0 for s in src)                      # zero-score offenses are never shown
    assert retrieve(STORY, r, k=1, min_score=0.0)[0].offense_id == src[0].offense_id
    assert retrieve(STORY, r, k=8, min_score=99.0) == []


def test_prompt_shows_numbered_sources_with_statute():
    src = retrieve(STORY, retriever(), k=8, min_score=0.0)
    user = build_messages(STORY, src)[1]["content"]
    assert STORY in user and "[1]" in user and "ตัวบท" in user


# ------------------------------------------------------------------ answer
def test_citations_map_to_offenses_and_code_computes_penalty():
    r = retriever()
    src = retrieve(STORY, r, k=8, min_score=0.0)
    n = {s.offense_id: s.n for s in src}
    llm = FakeLLM(rag_reply(n["no_helmet"], n["red_light"]))
    res = answer(STORY, r, k=8, min_score=0.0, client=llm)
    assert sorted(v.offense_id for v in res.verdict.violations) == ["no_helmet", "red_light"]
    assert {v.citation_key for v in res.verdict.violations} == {"land-traffic-2522:122", "land-traffic-2522:22"}
    assert res.penalty.total_fine_max == 6000 and res.penalty.total_points == 3
    assert res.llm_calls == 1 and "tools" not in llm.requests[0]


def test_unknown_source_number_is_dropped():
    llm = FakeLLM(rag_reply(1, 42))
    res = answer(STORY, retriever(), k=8, min_score=0.0, client=llm)
    assert len(res.verdict.violations) == 1
    assert any("[42]" in note for note in res.notes)


def test_nothing_above_the_floor_refuses_without_calling_the_model():
    llm = FakeLLM()                                           # would raise if called
    res = answer(STORY, retriever(), min_score=99.0, client=llm)
    assert res.refused and res.verdict.status == "out_of_scope" and res.verdict.summary_th == REFUSAL_SUMMARY
    assert res.llm_calls == 0 and not llm.requests


def test_streamed_reply_is_parsed_and_repaired_if_needed():
    r = retriever()
    tokens = []
    res = answer(STORY, r, k=8, min_score=0.0, client=StreamingFakeLLM(rag_reply(1)), on_token=tokens.append)
    assert len(tokens) > 1 and res.verdict.violations and res.llm_calls == 1
    res = answer(STORY, r, k=8, min_score=0.0, client=StreamingFakeLLM(final_msg("ผิดแน่นอน"), rag_reply(1)),
                 on_token=lambda t: None)
    assert res.verdict.violations and res.llm_calls == 2


# ------------------------------------------------------------------ web app (SSE)
def events(resp):
    out = []
    for frame in resp.text.split("\n\n"):
        if frame.startswith("data: ") and frame[6:] != "[DONE]":
            out.append(json.loads(frame[6:]))
    assert resp.text.rstrip().endswith("data: [DONE]")
    return out


def test_check_endpoint_streams_sources_tokens_and_verdict(monkeypatch):
    monkeypatch.setitem(webapp.state, "retriever", retriever())
    monkeypatch.setitem(webapp.state, "client", StreamingFakeLLM(rag_reply(1)))
    monkeypatch.setenv("RAG_MIN_SCORE", "0")
    from traffic_law.config import get_settings
    get_settings.cache_clear()
    try:
        resp = TestClient(webapp.app).post("/api/check", json={"story": STORY, "mode": "rag"})
    finally:
        get_settings.cache_clear()
    assert resp.status_code == 200 and resp.headers["content-type"].startswith("text/event-stream")
    ev = events(resp)
    types = [e["type"] for e in ev]
    assert types[0] == "sources" and "token" in types and types[-1] == "verdict"
    v = ev[-1]
    assert v["status"] == "violations_found" and v["violations"][0]["points"] and v["penalty"]


def test_check_endpoint_reports_errors_in_the_stream(monkeypatch):
    monkeypatch.setitem(webapp.state, "retriever", retriever())
    monkeypatch.setitem(webapp.state, "client", FakeLLM())       # runs out of replies -> error frame
    ev = events(TestClient(webapp.app).post("/api/check", json={"story": STORY, "mode": "baseline"}))
    assert ev[-1]["type"] == "error"


def test_check_endpoint_validates_input():
    assert TestClient(webapp.app).post("/api/check", json={"story": "", "mode": "rag"}).status_code == 422
    assert TestClient(webapp.app).post("/api/check", json={"story": "x", "mode": "magic"}).status_code == 422
