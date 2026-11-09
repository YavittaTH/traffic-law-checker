# Paired test on exact match (exact McNemar, two-sided)

Sources: results_agent_e3, results_rag, results_agent_heldout. RAG was not run on held-out.

| comparison | set | n | correct A | correct B | only A right | only B right | p | Holm p |
|---|---|---|---|---|---|---|---|---|
| agent vs baseline | main + held-out | 41 | 35 | 32 | 5 | 2 | 0.4531 | 0.4531 |
| agent vs rag | main | 31 | 27 | 18 | 11 | 2 | 0.0225 | 0.0674 |
| baseline vs rag | main | 31 | 24 | 18 | 9 | 3 | 0.1460 | 0.2920 |

## Discordant stories

- **agent vs baseline**: only A right ['h06', 's03', 's08', 's13', 's20']; only B right ['h03', 's31']
- **agent vs rag**: only A right ['s01', 's03', 's05', 's06', 's13', 's15', 's20', 's25', 's26', 's28', 's30']; only B right ['s09', 's16']
- **baseline vs rag**: only A right ['s01', 's05', 's06', 's15', 's25', 's26', 's28', 's30', 's31']; only B right ['s08', 's09', 's16']
