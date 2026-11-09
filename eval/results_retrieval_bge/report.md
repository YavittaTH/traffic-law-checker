# Retrieval — scenarios.jsonl (20 queries)

dense index: yes (BAAI/bge-m3)

tuning freeze: frozen at 2026-10-31T16:12+07:00 · unchanged: src/traffic_law/retrieval/legal_terms.py · unchanged: src/traffic_law/retrieval/offenses.py · unchanged: data/penalties.csv

| mode | recall@1 | recall@3 | recall@5 | recall@8 | all-found@5 | MRR | recall@5 95% CI |
|---|---|---|---|---|---|---|---|---|
| bm25_raw | 17.5% | 27.5% | 27.5% | 27.5% | 25.0% | 0.253 | 10%–48% |
| bm25 | 35.0% | 47.5% | 52.5% | 52.5% | 45.0% | 0.525 | 32%–72% |
| dense | 37.5% | 40.0% | 42.5% | 52.5% | 40.0% | 0.478 | 22%–65% |
| hybrid | 32.5% | 42.5% | 45.0% | 50.0% | 35.0% | 0.464 | 25%–65% |

## Offense catalogue (20 queries)

| mode | recall@1 | recall@3 | recall@5 | all-found@5 | MRR | recall@5 95% CI |
|---|---|---|---|---|---|---|
| bm25_raw | 30.0% | 44.2% | 51.7% | 45.0% | 0.496 | 31%–72% |
| bm25 | 44.2% | 58.3% | 75.0% | 70.0% | 0.700 | 57%–90% |
| dense | 64.2% | 85.8% | 88.3% | 75.0% | 0.910 | 79%–98% |
| hybrid | 44.2% | 80.8% | 90.0% | 85.0% | 0.784 | 78%–100% |
