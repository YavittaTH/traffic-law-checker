# ชุดทดสอบ (gold set)

ไฟล์ JSONL หนึ่งบรรทัดต่อหนึ่งสถานการณ์ เขียนเองโดยอิงตัวบทที่อยู่ใน corpus เท่านั้น

```json
{"id": "s001", "scenario": "ขี่มอเตอร์ไซค์ซ้อนสาม ไม่ใส่หมวกทั้งคนขี่และคนซ้อน", "expected": ["<offense_id>", "<offense_id>"], "status": "violations_found", "tags": ["motorcycle", "multi"]}
{"id": "s002", "scenario": "จอดรถริมถนนในที่ที่ไม่มีป้ายห้ามจอด", "expected": [], "status": "no_violation", "tags": ["parking", "negative"]}
{"id": "s003", "scenario": "ขับรถชนรถคันอื่นแล้วไปต่อ", "expected": ["<offense_id>"], "status": "violations_found", "tags": ["hit-and-run"]}
```

- `expected` ใช้ `offense_id` จาก `data/penalties.csv` ทำให้วัดผลได้ทั้งระดับความผิดและคำนวณค่าปรับ/แต้มเทียบได้
- `status`: `violations_found` / `no_violation` / `need_more_info` / `out_of_scope`

## ขั้นตอนกัน bias (ทำตามลำดับ)

1. **ล็อกการปรับระบบ** — `eval/frozen.json` เก็บ hash ของ `legal_terms.py`, `offenses.py`, `penalties.csv` (ล็อกเมื่อ 2026-10-31 16:12) รายงานผลทุกฉบับพิมพ์สถานะนี้ไว้บรรทัดบน ถ้าขึ้น `CHANGED since freeze` ต้องระบุในรายงาน
2. **คนเขียนข้อสอบไม่เห็นตารางแปลงคำ** — เขียนผ่านหน้า "เขียนข้อสอบกฎจราจร" (artifact) ซึ่งให้เขียนเรื่องก่อน แล้วจึงเห็นรายชื่อข้อหาเพื่อเลือกคำตอบ
3. **ชุดหลัก** (`scenarios.jsonl`) ใช้ปรับ agent ได้ ส่วน **held-out** (`heldout.jsonl`) ห้ามดูผลระหว่างพัฒนา รันครั้งเดียวตอนท้าย และห้ามแก้ระบบหลังเห็นผล
4. ชุด `dev_retrieval.jsonl` (18 ข้อ ผู้พัฒนาเขียนเอง) ใช้แค่ debug ห้ามใช้เป็นผลในรายงาน

## แบ่งชุด (บทเรียนจาก movie-finder)

| ไฟล์ | ใช้ทำอะไร |
|---|---|
| `scenarios.jsonl` | ชุดหลัก ใช้ตัดสินใจทุกอย่างระหว่างจูน |
| `heldout.jsonl` | เขียนแยก **ก่อน** เริ่มจูน แล้วรันครั้งเดียวตอนท้าย |

ควรมีอย่างน้อย: สถานการณ์ผิดข้อเดียว, ผิดหลายข้อพร้อมกัน, ไม่ผิด (negative), ข้อมูลไม่พอ, นอกขอบเขต (เช่น ถามเรื่องประกันภัย หรือกฎหมายต่างประเทศ) และใช้ภาษาพูด/สะกดผิดปนบ้าง

## Metrics

- ระดับความผิด: precision, recall, F1 (micro + macro), exact-set match
- `status` accuracy และอัตรา "ไม่ผิด" ที่ตอบถูก (กัน false positive)
- citation precision: มาตราที่อ้างมีอยู่จริงและรองรับความผิดนั้น
- retrieval: recall@k ของมาตราที่เกี่ยวข้อง
- baseline: LLM อย่างเดียว (ไม่มี RAG/tools) เทียบกับ agent
