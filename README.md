# MAMO Engine

**Multi-Agent Modular Orchestration** — a Rogue Night Pty Ltd engine that turns a messy business problem into business processes and requirements, with every requirement traceably linked back to its source.

```
Problem statement → Capabilities → Processes → Requirements → Trace matrix
        (each link verified, each run repeatable, any industry)
```

Owned by Rogue Night Pty Ltd. Proprietary, all rights reserved. This repo holds the **generic engine only**. It must never contain client documents, client data or client-specific deliverables (see [docs/DATA_AND_IP_POLICY.md](docs/DATA_AND_IP_POLICY.md)).

## What's in here

| Path | Purpose |
|---|---|
| [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md) | Phased build plan, milestones and exit criteria |
| [docs/BUILD_PLAN_P0-3.md](docs/BUILD_PLAN_P0-3.md) | Task-level plan for Phases 0–3 (Nov 2026 – Jan 2027) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Agents, trace-graph state store, schemas, orchestration |
| [docs/CLIENT_PLAYBOOK.md](docs/CLIENT_PLAYBOOK.md) | How to run the engine on a new client engagement |
| [docs/DATA_AND_IP_POLICY.md](docs/DATA_AND_IP_POLICY.md) | What may and may not enter this repo |
| [experiments/LOG_TEMPLATE.md](experiments/LOG_TEMPLATE.md) | One entry per experiment, dated, in Git |
| [benchmarks/README.md](benchmarks/README.md) | Rogue Night-owned gold-standard test cases |

## Status

Plan approved 4 Nov 2026. Repo: `nghilinh-alt/ProcessAndRequirementsBuilder` (private; moves to a Rogue Night organisation later). The structured build starts in Nov 2026 (earlier informal prototyping is background only), with the benchmark and baseline in Nov–Dec 2026.

## Ground rules

1. Engine code is domain-agnostic. Industry knowledge enters through **domain packs** (config), never hard-coded prompts.
2. Client work runs in a **separate private workspace** that pulls the engine in. Client outputs never get committed here.
3. Every experiment gets a log entry and a dated commit. That history is the evidence.
