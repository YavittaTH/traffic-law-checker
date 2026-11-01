# Agent evaluation — scenarios.jsonl (31 stories)

model: gemma-4-E4B-it · run at 2026-10-31T12:40+00:00

tuning freeze: frozen at 2026-10-31T16:12+07:00 · unchanged: src/traffic_law/retrieval/legal_terms.py · unchanged: src/traffic_law/retrieval/offenses.py · unchanged: data/penalties.csv

| system | status acc | offense P | offense R | offense F1 | exact match | exact 95% CI |
|---|---|---|---|---|---|---|
| rag | 71.0% | 82.8% | 80.0% | 81.4% | 58.1% | 42%–74% |

## Exact match by tag

| tag | n | rag |
|---|---|---|
| multi | 9 | 67% |
| multi_fact | 1 | 100% |
| need_info | 3 | 0% |
| negation | 4 | 100% |
| no_keyword | 8 | 50% |
| number_words | 1 | 0% |
| out_of_scope | 4 | 25% |
| single | 11 | 64% |
| slang | 1 | 100% |
| typo | 1 | 100% |

## Classic RAG behaviour

- k=8, min_score=1.0
- gold offenses that reached the sources: 25/30 (the model cannot answer an offense it was not shown)
- refused (nothing above the floor, no LLM call): 0
- mean seconds: 2.8
- answers changed by the grounding check: 0
