"""Web app: one page + one streaming endpoint (Server-Sent Events), like the course demo.

    python scripts/serve.py            # http://localhost:8000

POST /api/check  {"story": "...", "mode": "rag" | "agent" | "baseline"}
streams `data: {json}\\n\\n` frames, then `data: [DONE]`:
  {"type": "sources", "sources": [...]}       rag: the numbered sources the model will see
  {"type": "token", "text": "..."}            rag: the model's reply as it is generated
  {"type": "step", "tool": ..., "args": ...}  agent: each tool call as it happens
  {"type": "verdict", ...}                    the final answer + code-computed penalty
  {"type": "error", "message": "..."}
The `mode` switch is the demo's `use_rag` toggle: the same story with and without retrieval.

The model work is blocking, so it runs in a worker thread that pushes frames into a queue;
the response iterates the queue.
"""
from __future__ import annotations

import json
import queue
import threading
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from ..config import get_settings
from ..data.penalties import summarize

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="ทำแบบนี้ผิดอะไรบ้าง? — Thai traffic-law checker")

# Overridable for tests: a retriever and an LLM client (None = the real proxy client).
state: dict = {"retriever": None, "client": None}


def get_retriever():
    if state["retriever"] is None:
        from ..retrieval.retriever import load_retriever
        state["retriever"] = load_retriever(with_dense=False)
    return state["retriever"]


class CheckRequest(BaseModel):
    story: str = Field(min_length=1, max_length=2000)
    mode: Literal["rag", "agent", "baseline"] = "rag"


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    s = get_settings()
    r = get_retriever()
    return {"ok": True, "llm_configured": bool(s.openai_api_key and s.openai_base_url), "model": s.llm_model,
            "sections": len(r.sections), "offenses": len(r.rules), "rag_k": s.rag_k,
            "rag_min_score": s.rag_min_score}


def _frame(obj) -> str:
    return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"


def _verdict_event(verdict, penalty, retriever, **extra) -> dict:
    rules = retriever.rules
    viols = []
    for v in verdict.violations:
        r = rules.get(v.offense_id)
        sec = retriever.sections.get(v.citation_key)
        viols.append({**v.model_dump(), "description": r.description if r else v.offense_id,
                      "citation_label": (sec.label if sec else (f"พ.ร.บ.รถยนต์ มาตรา {r.section}" if r else "")),
                      "fine_max": r.fine_max if r else None, "jail_max_months": r.jail_max_months if r else None,
                      "points": r.points if r else None})
    return {"type": "verdict", "status": verdict.status, "summary_th": verdict.summary_th,
            "follow_up_question": verdict.follow_up_question, "violations": viols,
            "penalty": penalty.model_dump() if penalty else None, **extra}


def _work(req: CheckRequest, out: queue.Queue) -> None:
    put = lambda obj: out.put(_frame(obj))                     # noqa: E731
    try:
        r = get_retriever()
        client = state["client"]
        if req.mode == "rag":
            from ..rag import answer, retrieve
            sources = retrieve(req.story, r)
            put({"type": "sources", "sources": [s.to_dict() for s in sources]})
            res = answer(req.story, r, client=client, on_token=lambda t: put({"type": "token", "text": t}))
            put(_verdict_event(res.verdict, res.penalty, r, refused=res.refused, notes=res.notes,
                               llm_calls=res.llm_calls, seconds=round(res.seconds, 1)))
        elif req.mode == "agent":
            from ..agent.loop import run_agent

            def on_step(step):
                put({"type": "step", "tool": step.tool, "args": step.args, "result": step.result[:1500]})
            res = run_agent(req.story, r, client=client, on_step=on_step)
            put(_verdict_event(res.verdict, res.penalty, r, notes=res.notes, llm_calls=res.llm_calls,
                               seconds=round(res.seconds, 1)))
        else:
            from ..agent.baseline import run_baseline
            v, secs = run_baseline(req.story, r.rules, client=client)
            ids = [x.offense_id for x in v.violations]
            penalty = summarize(ids, r.rules) if ids else None
            put(_verdict_event(v, penalty, r, notes=["LLM อย่างเดียว: ไม่มีการค้นและไม่ตรวจการอ้างอิง"],
                               llm_calls=1, seconds=round(secs, 1)))
    except Exception as e:                                      # surface it in the page, not a dead stream
        put({"type": "error", "message": f"{type(e).__name__}: {e}"})
    finally:
        out.put(None)


@app.post("/api/check")
def check(req: CheckRequest):
    out: queue.Queue = queue.Queue()
    threading.Thread(target=_work, args=(req, out), daemon=True).start()

    def stream():
        while (item := out.get()) is not None:
            yield item
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
