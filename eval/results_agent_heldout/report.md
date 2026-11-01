# Agent evaluation — heldout.jsonl (10 stories)

model: gemma-4-E4B-it · run at 2026-10-31T10:18+00:00

tuning freeze: frozen at 2026-10-31T16:12+07:00 · unchanged: src/traffic_law/retrieval/legal_terms.py · unchanged: src/traffic_law/retrieval/offenses.py · unchanged: data/penalties.csv

| system | status acc | offense P | offense R | offense F1 | exact match | exact 95% CI |
|---|---|---|---|---|---|---|
| agent | 90.0% | 88.9% | 80.0% | 84.2% | 80.0% | 50%–100% |
| baseline | 90.0% | 88.9% | 80.0% | 84.2% | 80.0% | 50%–100% |

## Exact match by tag

| tag | n | agent | baseline |
|---|---|---|---|
| multi | 3 | 100% | 67% |
| need_info | 1 | 100% | 100% |
| negation | 2 | 100% | 100% |
| no_keyword | 2 | 0% | 50% |
| number_words | 1 | 100% | 100% |
| out_of_scope | 1 | 100% | 100% |
| single | 3 | 33% | 67% |
| typo | 1 | 100% | 100% |

## Agent behaviour

- tool calls: {'search_offenses': 15}
- mean LLM calls per story: 3.1 · mean seconds: 3.3
- answers changed by the grounding check: 0 (offenses dropped: 0)
