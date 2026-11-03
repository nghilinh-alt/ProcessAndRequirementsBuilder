# MAMO Engine — Build Plan

**Owner:** Rogue Night Pty Ltd (Linh Nghi, director)
**Prepared:** 4 Nov 2026 · **Status:** DRAFT for Linh's review
**Horizon:** Nov 2026 – Jun 2027 (engine v1), then client-ready packaging

---

## 1. Goal

A reusable engine Rogue Night can point at any client's business problem and get back:

- a structured problem statement and capability map
- business processes (steps, actors, inputs/outputs)
- requirements with stable IDs (functional + non-functional)
- a trace matrix linking every requirement to its process, capability and source text
- a confidence/verification report showing which links were checked and which need a human

Targets come from the FY26-27 R&D plan (H1–H5) and act as the engine's quality bar:

| Measure | Target |
|---|---|
| Coverage of gold-standard requirements | ≥ 85% |
| Invalid / duplicate requirements | ≤ 10% |
| Trace-link precision / recall | ≥ 90% / ≥ 85% |
| Orphan requirements | < 5% |
| Token use per stage | roughly flat across stages |
| Run-to-run agreement (5 runs) | ≥ 90% |
| Accuracy drop on an unseen domain | ≤ 10 pts |

These are *hypotheses*, not promises. The plan is built so that missing a target produces a logged finding and a design change, not a dead end.

---

## 2. Phases

### Phase 0 — Repo, records and Round 0 write-up (Nov 2026, week 1–2)
- Create this repo; protect `main`; one branch per experiment (`exp/MAMO-RT-0X`).
- Write the Round 0 summary (Aug–Oct 2026) **from existing evidence only**, labelled "written Nov 2026".
- Set up the timesheet and experiment log (`experiments/`).
- **Exit:** repo live, Round 0 note committed, log template in use.

### Phase 1 — Core schemas and trace-graph store (Nov 2026)
- Define typed artefacts: `Problem`, `Capability`, `Process`, `Step`, `Requirement`, `TraceLink`, `Run`.
- ID rules (for example `CAP-001`, `PRC-003.2`, `REQ-F-014`) and a canonicalisation function.
- Store: SQLite to start (nodes, links, runs, token_usage tables). Swap later only if experiments show a need.
- **Exit:** schemas validated by tests; store can round-trip a hand-made case.

### Phase 2 — Benchmarks and scoring harness (Nov–Dec 2026)
- Three Rogue Night-built cases (no client data): synthetic insurance claims finance (benchmark), app product development (transfer A), small retail (transfer B).
- Each: problem text, expert processes, requirements, trace matrix.
- Scoring scripts: coverage, invalid/duplicate rate, link precision/recall, orphans, tokens, latency, $/run, run-to-run agreement.
- Transfer-domain gold standards kept in a locked folder, not read during tuning.
- **Exit:** `score` command produces a metrics report for any run.

### Phase 3 — Baseline (Dec 2026)
- Single agent, single prompt: problem → requirements + links.
- Score against all three cases. Commit the report.
- **Exit:** baseline numbers logged as MAMO-RT-01.

### Phase 4 — Staged pipeline + verifier (Jan–Feb 2027)
- Agents: Intake → Capability → Process → Requirements → **Verifier**.
- Ablations: with/without verifier; sequential vs hierarchical orchestration.
- **Exit:** H1/H2 results logged; chosen orchestration recorded with reasons.

### Phase 5 — State design (Feb–Mar 2027)
- Compare: full-memory carry-forward (FY25-26 approach) vs summarised memory vs trace-graph store (agents read/write typed nodes only).
- Measure tokens, latency and accuracy per stage.
- **Exit:** H3 result logged; default state mode chosen.

### Phase 6 — Repeatability (Mar–Apr 2027)
- Controls: fixed schemas, ID rules, temperature/seed, canonicaliser, deterministic ordering.
- 5 runs per case per setting; measure agreement.
- **Exit:** H4 result logged; default control profile chosen.

### Phase 7 — Cross-domain transfer (Apr–Jun 2027)
- Freeze the pipeline. Run on app-dev and retail cases. Unlock their gold standards only for scoring.
- Failure analysis by stage and cause.
- **Exit:** H5 result logged; list of domain-specific failure types → domain-pack design.

### Phase 8 — Client packaging (Jul 2027 onward, *not R&D*)
- CLI + simple config to run on a client problem.
- Exporters: Markdown BRD, CSV/XLSX trace matrix, optional Airtable push.
- Domain-pack format (glossary, typical actors, NFR checklist) so new industries are config, not code.
- Human review step: verifier flags low-confidence links for a BA to accept/reject.
- **Exit:** first paid engagement delivered from a separate client workspace.

> Phases 3–7 are the experimental work. Phases 0–2 are supporting. Phase 8 and all client delivery are ordinary commercial work. Keep hours and costs tagged by phase so the split is easy later.

---

## 3. Milestones

| Date | Milestone |
|---|---|
| mid-Nov 2026 | Repo live, Round 0 note, schemas drafted |
| end-Dec 2026 | Benchmarks + scoring harness + baseline report |
| end-Feb 2027 | Pipeline + verifier results (H1/H2) |
| end-Mar 2027 | State design result (H3) |
| end-Apr 2027 | Repeatability result (H4) |
| end-Jun 2027 | Transfer result (H5); engine v1 frozen |
| Q3 2027 | Client-ready package (v1.0) |

---

## 4. Tech stack (proposed — confirm)

- **Language:** Python 3.12, Pydantic for schemas, pytest.
- **Models:** Claude API primary; provider wrapper so OpenAI can be swapped in for comparison.
- **Orchestration:** thin in-house orchestrator first (stages as functions over the store). Bring in a framework only if an experiment needs it; FY25-26 notes on crewAI/AutoGen state issues are the reason not to start there.
- **Store:** SQLite → Postgres only if needed.
- **Logging:** every LLM call logs model, prompt hash, tokens in/out, latency, cost, run ID.
- **Config:** YAML for pipelines, control profiles and domain packs.

---

## 5. Risks

| Risk | Mitigation |
|---|---|
| Client IP or data leaks into the engine | Data policy, `.gitignore` on `clients/`, pre-commit check for client names |
| Gold standards are too easy or biased | Optional external BA validation; hidden transfer sets |
| Existing tool already solves traceability | Prior-knowledge search (Nov 2026); narrow scope to what's still unknown |
| Token cost of repeat runs | Budget per experiment; cache identical calls; use smaller models for baselines |
| Scope creep into UI/product polish | Phase 8 only; keep it out of experiment branches |

---

## 6. Open decisions for Linh

1. Confirm stack (section 4).
2. Repo name and GitHub owner (personal account or a `rogue-night` organisation; an org is better for client reuse and later hires).
3. Visibility: **private** recommended.
4. Licence: proprietary/all-rights-reserved (default here) unless you plan to open-source parts.
5. Whether to bring in an external BA to validate the benchmark gold standards.
