# Retrieval — dev_retrieval.jsonl (18 queries)

dense index: not built

tuning freeze: frozen at 2026-10-31T16:12+07:00 · unchanged: src/traffic_law/retrieval/legal_terms.py · unchanged: src/traffic_law/retrieval/offenses.py · unchanged: data/penalties.csv

| mode | recall@1 | recall@3 | recall@5 | recall@8 | all-found@5 | MRR | recall@5 95% CI |
|---|---|---|---|---|---|---|---|---|
| bm25_raw | 36.1% | 38.0% | 43.5% | 43.5% | 38.9% | 0.425 | 22%–64% |
| bm25 | 58.3% | 81.5% | 83.3% | 83.3% | 83.3% | 0.720 | 67%–100% |

## Offense catalogue (18 queries)

| mode | recall@1 | recall@3 | recall@5 | all-found@5 | MRR | recall@5 95% CI |
|---|---|---|---|---|---|---|
| bm25_raw | 54.6% | 73.1% | 77.8% | 77.8% | 0.701 | 56%–94% |
| bm25 | 93.5% | 100.0% | 100.0% | 100.0% | 1.000 | 100%–100% |
