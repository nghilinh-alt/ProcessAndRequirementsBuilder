# MAMO Engine — Architecture (target design)

Draft, 4 Nov 2026. Expect experiments in Phases 4–7 to change this; record each change in the experiment log and update this file in the same commit.

## 1. Pipeline

```
                 ┌──────────────── Trace-graph store (SQLite) ────────────────┐
                 │  nodes(id, type, text, source_span, run_id, stage)          │
                 │  links(from_id, to_id, kind, confidence, verified, run_id)  │
                 │  runs(id, config_hash, model, seed, started, cost)          │
                 └──────▲──────────▲──────────▲──────────▲──────────▲─────────┘
                        │          │          │          │          │
 Problem text ─► [Intake] ─► [Capability] ─► [Process] ─► [Requirements] ─► [Verifier] ─► [Canonicaliser] ─► Exports
```

Each agent **reads only the nodes it needs** from the store and **writes typed nodes and links** back. No agent receives the full transcript of earlier stages. This is the design H3 tests against the FY25-26 full-memory approach.

## 2. Agents

| Agent | Reads | Writes |
|---|---|---|
| Intake | raw problem text | `Problem` nodes with source spans; actors, goals, constraints |
| Capability | Problem nodes | `Capability` nodes + `problem→capability` links |
| Process | Capabilities | `Process`/`Step` nodes + `capability→process` links |
| Requirements | Processes/Steps | `Requirement` nodes (F/NFR) + `process→requirement` links |
| Verifier | One link + both endpoints + source span | `verified`, `confidence`, reason; flags invented, missing or merged links |
| Canonicaliser | Whole graph | Stable IDs, deduped requirements, sorted output (for repeatability) |

## 3. Schemas (sketch)

```python
class Requirement(BaseModel):
    id: str            # REQ-F-014 / REQ-N-003
    kind: Literal["functional", "non_functional"]
    statement: str     # "The system shall…"
    acceptance: list[str]
    source_process: str
    rationale: str

class TraceLink(BaseModel):
    from_id: str
    to_id: str
    kind: Literal["problem_capability", "capability_process", "process_requirement"]
    confidence: float
    verified: bool | None
    verifier_note: str | None
```

## 4. Configuration

```
config/
  pipelines/       sequential.yaml, hierarchical.yaml
  controls/        default.yaml (temperature, seed, schema strictness)
  state/           full_memory.yaml, summarised.yaml, trace_graph.yaml
domain_packs/
  _generic.yaml    always loaded
  <industry>.yaml  glossary, typical actors, NFR checklist (optional)
```

## 5. Outputs

- `requirements.md`: BRD-style document
- `trace_matrix.csv`: one row per requirement with its full upstream chain
- `verification_report.md`: unverified/low-confidence links for human review
- `run_metrics.json`: tokens, latency and cost per stage

## 6. Planned repo layout

```
src/mamo/
  schemas.py  store.py  orchestrator.py  llm.py
  agents/{intake,capability,process,requirements,verifier}.py
  canonicalise.py  export/
eval/        scoring scripts
benchmarks/  gold-standard cases (Rogue Night-owned)
experiments/ dated logs, one per experiment
config/  domain_packs/  tests/
```
