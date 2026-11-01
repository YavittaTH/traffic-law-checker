"""Ask the agent about one story and see every step.

    python scripts/ask.py "ขี่มอไซค์ซ้อนแฟน ไม่ใส่หมวกทั้งคู่ แล้วฝ่าไฟแดง"
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traffic_law.agent.loop import run_agent  # noqa: E402
from traffic_law.retrieval.retriever import load_retriever  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('usage: python scripts/ask.py "เรื่องที่เกิดขึ้น"')
    r = load_retriever(with_dense=False)
    res = run_agent(sys.argv[1], r, on_step=lambda st: print(f"→ {st.tool}({st.args})\n   {st.result[:220]}…"))
    v = res.verdict
    print(f"\nstatus: {v.status}\nสรุป: {v.summary_th}")
    for x in v.violations:
        rule = r.rules[x.offense_id]
        print(f"  • {rule.description}  [{x.citation_key}]  — {x.reason}")
    if v.follow_up_question:
        print(f"ถามเพิ่ม: {v.follow_up_question}")
    if res.penalty:
        p = res.penalty
        print(f"ค่าปรับสูงสุดตามกฎหมาย รวม {p.total_fine_max:,} บาท"
              + (f" (+ข้อหาที่ไม่มีตัวเลข: {', '.join(p.fine_unknown)})" if p.fine_unknown else "")
              + f" · ตัด {p.total_points} คะแนน" + (" (ถึงเพดาน 8)" if p.points_capped else "")
              + f" · เหลือ {p.points_left}" + (" · มีโทษจำคุก" if p.any_jail else ""))
        print("  (เป็นเพดานสูงสุดที่กฎหมายกำหนด ค่าปรับจริงตามใบสั่งมักต่ำกว่านี้)")
        if p.unverified:
            print(f"⚠ ยังไม่ได้ตรวจกับตัวบท: {', '.join(p.unverified)}")
    if res.notes:
        print("grounding:", "; ".join(res.notes))
    print(f"({res.llm_calls} LLM calls, {res.seconds:.1f}s)")


if __name__ == "__main__":
    main()
