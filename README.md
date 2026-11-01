# 🚦 Traffic Law Checker — "ทำแบบนี้ผิดอะไรบ้าง?"

เล่าเหตุการณ์บนถนนเป็นภาษาพูด แล้วระบบจะบอกว่าคนขับผิดกฎหมายจราจร **ข้อไหนบ้าง** อ้างมาตราจากตัวบทจริง และคำนวณค่าปรับสูงสุดรวมกับแต้มที่ถูกตัดด้วยโค้ด ถ้าข้อมูลไม่พอจะถามกลับ ถ้าไม่ผิดจะตอบว่าไม่ผิด และถ้าเป็นเรื่องนอกตารางจะบอกว่านอกขอบเขต

> LLM course capstone · ไม่ใช่คำปรึกษาทางกฎหมาย · ใช้ kmitl-llm-app-demo และ movie-finder เป็นแบบอย่างของ pattern เท่านั้น

## สามระบบที่เทียบกัน

| ระบบ | ไฟล์ | ทำงานอย่างไร |
|---|---|---|
| **LLM อย่างเดียว** (baseline) | `agent/baseline.py` | ไม่ค้น: รายชื่อข้อหา 23 แถวอยู่ใน prompt เรียกโมเดลครั้งเดียว |
| **RAG** (แบบเดียวกับ demo ของวิชา) | `rag.py` | ค้นครั้งเดียวด้วยคำของผู้ใช้ → แหล่งข้อมูลที่ผ่าน `min_score` เป็นรายการมีหมายเลข → โมเดลตอบโดยอ้าง `[n]` → ไม่มีอะไรผ่านเกณฑ์ = ปฏิเสธโดยไม่เรียกโมเดล |
| **Agentic RAG** | `agent/loop.py` | โมเดลเขียนคำค้นเป็นภาษากฎหมายเองและเรียกเครื่องมือค้นได้หลายรอบ (≤6) |

ทั้ง RAG และ agent ผ่าน **grounding** เดียวกัน (ข้อหาต้องมาจากผลค้นจริง มาตราที่อ้างต้องเป็นมาตราที่ค้นเจอ) และ**ค่าปรับ/แต้มคำนวณด้วยโค้ด**จาก `data/penalties.csv` ไม่ให้โมเดลคิดเลข

```
เรื่อง (ภาษาพูด)
   │
   ├── RAG ──────── BM25 + ตารางแปลงคำ บนบัญชีข้อหา → top-8 ที่คะแนน ≥ 1.0
   │                → [1] ข้อหา · ระเบียบ · ตัวบท  [2] …  → LLM 1 ครั้ง ตอบ {"source": n}
   │
   └── Agent ────── LLM ↔ search_offenses / search_law / get_section / compute_penalty (≤6 รอบ)
   │
   ▼
grounding → ค่าปรับสูงสุด + แต้ม (เพดาน 8 ต่อครั้ง, ข้อเดียวในระเบียบนับครั้งเดียว) ด้วยโค้ด
```

## เริ่มต้น

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # แล้วใส่ OPENAI_API_KEY / OPENAI_BASE_URL ของ proxy วิชาใน .env เท่านั้น
pytest -q                         # ไม่ต้องใช้เน็ตหรือ API key
python scripts\build_corpus.py    # -> data/processed/sections.jsonl (221 chunk)
```

### เว็บแอป

```bash
python scripts\serve.py           # เปิด http://localhost:8000
```

พิมพ์เรื่อง เลือกโหมด **RAG / Agentic RAG / LLM อย่างเดียว** แล้วกด "ตรวจ" (หรือ Ctrl+Enter) หน้าเว็บรับผลแบบ streaming (SSE) จาก `POST /api/check`:
- โหมด RAG แสดงแหล่งข้อมูลที่ค้นเจอพร้อมหมายเลขและคะแนน BM25 ตามด้วยข้อความที่โมเดลกำลังสร้าง และไฮไลต์แหล่งที่ถูกอ้าง
- โหมด agent แสดงทุก tool call ตอนที่มันเกิด
- ทุกโหมดจบด้วยผลการตรวจ ค่าปรับสูงสุดรวม และแต้มที่ถูกตัด

สลับโหมดกับเรื่องเดิมเพื่อดูว่าการค้นช่วยอย่างไร แบบเดียวกับปุ่ม `use_rag` ของ demo

### บรรทัดคำสั่ง

```bash
python scripts\smoke_test_llm.py                                  # ต้องได้ [PASS] สามบรรทัด
python scripts\ask.py "ขี่มอไซค์ซ้อนแฟน ไม่ใส่หมวกทั้งคู่ แล้วฝ่าไฟแดง"    # ดูทุกขั้นของ agent
python scripts\search.py "ขี่มอไซค์ไม่ใส่หมวกแล้วฝ่าไฟแดง"            # ดูผลค้นอย่างเดียว
```

### วัดผล

```bash
python eval\run_retrieval.py                 # retrieval: recall@k ของข้อหาและมาตรา
python eval\run_min_score.py                 # เลือก k และ min_score ของ RAG (ไม่ใช้ LLM)
python eval\run_agent.py --mode rag --out eval\results_rag      # RAG บนชุดหลัก 31 ข้อ
python eval\run_agent.py --mode all --out eval\results_all      # สามระบบพร้อมกัน
```

กฎกัน bias (รายละเอียดใน `eval/README.md`):
- ไฟล์ที่ใช้จูนถูกล็อกด้วย hash (`eval/frozen.json`)
- ชุดข้อสอบเขียนหลังล็อกและผู้ใช้ตรวจครบแล้ว
- **held-out รันไปแล้วครั้งเดียว** (`eval/results_agent_heldout/`) RAG สร้างหลังเห็นผล held-out แล้ว ถ้าจะรัน RAG บน held-out ต้องใส่ `--final --posthoc` และรายงานจะติดป้าย POST-HOC

ผลทุกรอบอยู่ใน [`docs/experiments.md`](docs/experiments.md)

## สถานะ

- [x] corpus: พ.ร.บ.จราจรทางบก 2522 + ฉบับที่ 13 (consolidate ตามวรรค) + ระเบียบตัดคะแนน 2565 → 221 chunk
- [x] `data/penalties.csv`: 22 ข้อหา (23 แถว) **ตรวจกับตัวบทครบ 23/23**
- [x] retrieval: BM25 (pythainlp) + ตารางแปลงภาษาพูด→ภาษากฎหมาย + บัญชีข้อหา + dense/hybrid (RRF)
- [x] agent + grounding + baseline · ชุดหลัก 31 + held-out 10 (E2–E4)
- [x] RAG แบบ demo: numbered sources, `[n]` citations, `min_score` floor + sweep (E5)
- [x] FastAPI + SSE + หน้าเว็บ (สามโหมด)
- [x] เทียบสามระบบบนชุดหลัก (E6): agent 87.1% · LLM อย่างเดียว 77.4% · RAG 58.1% → agent เป็นระบบหลัก

## Layout

```
traffic-law-checker/
├── src/traffic_law/
│   ├── config.py        settings จาก .env (ที่เดียวที่อ่าน environment)
│   ├── llm.py           ที่เดียวที่เรียก LLM: chat, chat_stream (SSE), chat_json + repair
│   ├── schemas.py       Section, PenaltyRule, Verdict, PenaltySummary
│   ├── thai_text.py     เลขไทย, ซ่อมข้อความจาก PDF
│   ├── data/            statute (แยกมาตรา), consolidate (รวมฉบับแก้ไข), penalties (ตาราง + คำนวณ)
│   ├── retrieval/       tokenize, legal_terms, chunks, bm25, dense, offenses, retriever
│   ├── rag.py           RAG แบบ demo: retrieve → numbered context → cited answer
│   ├── agent/           tools, loop, grounding, baseline
│   └── api/             app.py (FastAPI + SSE), static/index.html
├── scripts/           build_corpus, build_index, search, smoke_test_llm, ask, serve
├── data/raw | processed | penalties.csv
├── eval/                gold sets, run_retrieval, run_min_score, run_agent, ผลแต่ละรอบ
├── docs/                data_notes.md, experiments.md
└── tests/               56 tests ด้วยข้อมูลสังเคราะห์และ LLM ปลอม ไม่ต้องใช้เน็ต
```

## ข้อจำกัด

- กฎหมายและอัตราค่าปรับเปลี่ยนได้ ระบบตอบตามฉบับที่อยู่ใน corpus ณ วันที่สร้างเท่านั้น
- ค่าปรับที่แสดงคือ**อัตราสูงสุดตามกฎหมาย** ไม่ใช่จำนวนที่จะถูกเปรียบเทียบปรับจริง
- ครอบคลุมเฉพาะ 22 ข้อหาที่ตัดคะแนน เรื่องอื่น (จอดรถ ภาษีรถ ไม่มีใบขับขี่ ฯลฯ) ตอบว่านอกขอบเขต
- การค้นใช้คำ (BM25) เรื่องที่ไม่มีคำหลักเลย เช่น "ตั้งวงแล้วขับกลับ" จึงหาข้อหาไม่เจอ และคำกำกวมอย่าง "ป้าย" ชี้ไปผิดข้อหาได้ (h03 ใน held-out)
