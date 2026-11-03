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
gold/processes.yaml
gold/requirements.yaml
gold/trace_matrix.csv
NOTES.md            who built it, when, assumptions, reviewer
```

Transfer-domain `gold/` folders are read only by the scoring scripts, never by prompts or tuning code.
