# Agent evaluation — scenarios.jsonl (31 stories)

model: gemma-4-E4B-it · run at 2026-10-31T10:04+00:00

tuning freeze: frozen at 2026-10-31T16:12+07:00 · unchanged: src/traffic_law/retrieval/legal_terms.py · unchanged: src/traffic_law/retrieval/offenses.py · unchanged: data/penalties.csv

| system | status acc | offense P | offense R | offense F1 | exact match | exact 95% CI |
|---|---|---|---|---|---|---|
| agent | 87.1% | 93.1% | 90.0% | 91.5% | 83.9% | 71%–97% |
| baseline | 87.1% | 92.3% | 80.0% | 85.7% | 77.4% | 61%–90% |

## Exact match by tag

| tag | n | agent | baseline |
|---|---|---|---|
| multi | 9 | 100% | 67% |
| multi_fact | 1 | 100% | 100% |
| need_info | 3 | 100% | 100% |
| negation | 4 | 100% | 100% |
| no_keyword | 8 | 50% | 50% |
| number_words | 1 | 100% | 100% |
| out_of_scope | 4 | 75% | 100% |
| single | 11 | 64% | 64% |
| slang | 1 | 100% | 100% |
| typo | 1 | 100% | 100% |

## Agent behaviour

- tool calls: {'search_offenses': 45, 'compute_penalty': 4}
- mean LLM calls per story: 3.0 · mean seconds: 3.2
- answers changed by the grounding check: 0 (offenses dropped: 0)
