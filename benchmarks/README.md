# Benchmarks

Rogue Night-owned gold-standard cases. No client documents or data.

| Case | Role | Status |
|---|---|---|
| `insurance_claims_finance/` | Benchmark domain (synthetic, type of problem only) | to build Nov 2026 |
| `app_product_dev/` | Transfer domain A, gold standard hidden during tuning | to build Nov–Dec 2026 |
| `small_retail/` | Transfer domain B, gold standard hidden during tuning | to build Nov–Dec 2026 |

Each case folder:

```
problem.md          the messy input
gold/processes.yaml     L2 → L3 → L4 hierarchy
gold/rules.yaml         business rules
gold/requirements.yaml
gold/trace_matrix.csv
gold/change_scenarios.yaml   for H6, added in Phase 8 (Apr–May 2027), before the engine runs on them
NOTES.md            who built it, when, assumptions, acceptance rules, re-review date
```

Transfer-domain `gold/` folders are read only by the scoring scripts, never by prompts or tuning code.

Gold standards are built and validated by Linh Nghi (BA). Write each case's acceptance rules before the engine runs on it, and re-review the gold standard at least a week after building it.
