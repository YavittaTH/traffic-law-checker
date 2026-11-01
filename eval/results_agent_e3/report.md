# Agent evaluation — scenarios.jsonl (31 stories)

model: gemma-4-E4B-it · run at 2026-10-31T10:11+00:00

tuning freeze: frozen at 2026-10-31T16:12+07:00 · unchanged: src/traffic_law/retrieval/legal_terms.py · unchanged: src/traffic_law/retrieval/offenses.py · unchanged: data/penalties.csv

| system | status acc | offense P | offense R | offense F1 | exact match | exact 95% CI |
|---|---|---|---|---|---|---|
| agent | 90.3% | 93.5% | 96.7% | 95.1% | 87.1% | 74%–97% |
| baseline | 87.1% | 92.6% | 83.3% | 87.7% | 77.4% | 61%–90% |

## Exact match by tag

| tag | n | agent | baseline |
|---|---|---|---|
| multi | 9 | 89% | 67% |
| multi_fact | 1 | 100% | 100% |
| need_info | 3 | 67% | 67% |
| negation | 4 | 100% | 100% |
| no_keyword | 8 | 88% | 62% |
| number_words | 1 | 100% | 100% |
| out_of_scope | 4 | 75% | 100% |
| single | 11 | 91% | 73% |
| slang | 1 | 100% | 100% |
| typo | 1 | 100% | 100% |

## Agent behaviour

- tool calls: {'search_offenses': 42, 'compute_penalty': 1}
- mean LLM calls per story: 2.8 · mean seconds: 4.9
- answers changed by the grounding check: 0 (offenses dropped: 0)
