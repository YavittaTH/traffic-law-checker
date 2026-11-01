"""Check the class LLM proxy before a long run: Thai chat, JSON output, tool calling.

    python scripts/smoke_test_llm.py        -> three [PASS] lines
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traffic_law.config import get_settings  # noqa: E402
from traffic_law.llm import chat, extract_json  # noqa: E402


def main() -> None:
    s = get_settings()
    s.require_llm()
    print(f"model {s.llm_model} at {s.openai_base_url}")
    ok = True

    m = chat([{"role": "user", "content": "ตอบสั้น ๆ ภาษาไทย: ฝ่าไฟแดงผิดกฎหมายไหม"}], max_tokens=80)
    good = bool(m.content and any("฀" <= ch <= "๿" for ch in m.content))
    print(f"[{'PASS' if good else 'FAIL'}] Thai chat: {(m.content or '')[:60]!r}"); ok &= good

    m = chat([{"role": "user", "content": 'Reply with ONLY this JSON: {"status": "ok", "n": 3}'}], max_tokens=40)
    try:
        good = extract_json(m.content).get("n") == 3
    except ValueError:
        good = False
    print(f"[{'PASS' if good else 'FAIL'}] JSON output: {(m.content or '')[:60]!r}"); ok &= good

    tools = [{"type": "function", "function": {"name": "search_offenses", "description": "search traffic offenses",
              "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}]
    m = chat([{"role": "user", "content": "ค้นหาข้อหาเรื่องขับรถขณะเมาสุรา โดยใช้เครื่องมือ"}], tools=tools, max_tokens=120)
    calls = getattr(m, "tool_calls", None) or []
    good = bool(calls) and calls[0].function.name == "search_offenses"
    print(f"[{'PASS' if good else 'FAIL'}] tool calling: "
          f"{[(c.function.name, json.loads(c.function.arguments or '{}')) for c in calls] or m.content!r}"); ok &= good
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
