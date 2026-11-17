# MAMO Engine — Detailed build plan, Phases 0–3 (Nov 2026 – Jan 2027)

**Prepared:** 4 Nov 2026 · **Status:** Approved by Linh Nghi, 4 Nov 2026 · **Revised:** 14 Nov 2026 (H3 scope: +L2–L4 process levels and business rules; schedule re-based after a ~1.5-week slip)
**Parent plan:** [BUILD_PLAN.md](BUILD_PLAN.md)
**Capacity:** ~6 hrs/week to 31 Dec 2026 (option (a), confirmed 4 Nov 2026). This includes Linh's own design and planning time away from the keyboard, not just sessions with Claude.

This plan covers everything up to and including the **single-agent baseline (MAMO-RT-01)**. That baseline is the yardstick every later experiment is measured against, so these phases are about building a reliable ruler, not a clever engine.

---

## 0. Summary

| Phase | What you end up with | Est. hours | Target finish | R&D type |
|---|---|---|---|---|
| 0 | Timesheet, prior-knowledge search, Python project skeleton | 6 | 8 Nov | Supporting / admin |
| 1 | Schemas (+ L2–L4 levels and business rules), ID rules, SQLite trace store, logged LLM wrapper | 14 | 29 Nov | Supporting |
| 2 | 3 gold-standard cases (with L2–L4 processes and rules) + scoring harness | 22 | 20 Dec | Supporting |
| 3 | Baseline runs, scored report, MAMO-RT-01 log | 6 | 31 Dec 2026 | **Core** |
| | **Total** | **~48** | | |

**Capacity (decided 4 Nov 2026):** option (a), ~6 hrs/week, so the baseline lands by **31 Dec 2026**. The hours count all R&D work on these tasks, including Linh's own thinking, sketching and planning done outside Claude sessions, as long as it's logged (see "Logging your own time" below).

The claim starts in **Nov 2026**; Aug–Oct 2026 work is not claimed (decided 4 Nov 2026). Phases 0–3 now need ~48 hrs (the H3 scope change on 14 Nov added ~5). At Linh's $70/hr rate, the FY26-27 $30k budget needs ~329 director hrs, so ~281 in Jan–Jun 2027 (**~10.8 hrs/week**). The $20k eligibility floor needs ~186 hrs, so ~138 in Jan–Jun (**~5.3 hrs/week**). The R&D plan §5.1 has the breakdown. Phase 4–7 plans will be sized to real experimental work, not to the dollar target.

## Week-by-week schedule (revised 14 Nov 2026)

Done by 14 Nov: Phase 0 (0.1–0.3, incl. Linh's 0.2 review) and 1.1 schemas. About 1.5 weeks behind the original schedule, and the narrowed H3 adds ~5 hrs. To keep the baseline by 31 Dec, the weeks to 20 Dec need **~7 hrs each**.

| Week | Tasks | Hrs |
|---|---|---|
| 4–15 Nov | 0.1, 0.2 (+ Linh's review), 0.3 → **Phase 0 done**; 1.1 schemas | done |
| 16–22 Nov | 1.1b schema extension (L2–L4, business rules); 1.2 ID rules + canonicaliser; 1.3 trace store | 7 |
| 23–29 Nov | 1.4 LLM wrapper; 1.5 mini fixture → **Phase 1 done**; 2.1 gold format; start 2.2 insurance case | 7 |
| 30 Nov–6 Dec | Finish 2.2; start 2.3 app-dev case | 7 |
| 7–13 Dec | Finish 2.3; 2.4 retail case | 6.5 |
| 14–20 Dec | Re-review insurance gold (≥1 week gap); 2.5 matcher, 2.6 metrics, 2.7 score CLI → **Phase 2 done**; 3.1 baseline agent | 7 |
| 21–27 Dec | Re-review transfer gold; 3.2 baseline runs; 3.3 judge spot-check (light week) | 2.5 |
| 28–31 Dec | 3.4 MAMO-RT-01 log → **Phase 3 done** | 2 |
| | **Remaining from 16 Nov** (no spare left) | **39** |

If a week slips, let 3.4 (and if needed 3.2–3.3) move to the first week of Jan 2027 rather than squeezing the gold standards. The gold standards are the ruler for every later result.

---

## Phase 0 — Records, skeleton, prior knowledge (4–8 Nov)

| # | Task | Hrs | Done when |
|---|---|---|---|
| 0.1 | **Timesheet**: create `admin/` outside the repo (or a spreadsheet) with columns *date, hours, phase, task #, experiment ref, R&D type, mode (own work / with Claude), what was worked out*. Start logging today. | 0.5 | First entry made |
| 0.2 | **Prior-knowledge search** (R&D plan §3): academic, commercial tools, open-source. Write dated notes to `research/prior_knowledge_2026-11.md`: what each source does, what it doesn't, and the remaining gap. | 4 | Notes committed; any narrowing of H1–H5 recorded |
| 0.3 | **Python skeleton**: `pyproject.toml` (Python 3.12+, pydantic, pytest, ruff), `src/mamo/__init__.py`, `tests/`, a `make test` or `pytest` that passes on an empty test. `.env.example` with `ANTHROPIC_API_KEY=`. | 1.5 | `pytest` green; pushed |

> **Note:** GitHub branch protection on a *private personal* repo needs a paid GitHub plan. Without one, stick to a working rule instead: do experiment work on `exp/…` branches and merge to `main` only once the log entry is written.

---

## Phase 1 — Schemas, store, LLM wrapper (9–29 Nov)

| # | Task | Hrs | Done when |
|---|---|---|---|
| 1.1 | **Schemas** (`src/mamo/schemas.py`): `Problem`, `Capability`, `Process`, `Step`, `Requirement`, `TraceLink`, `Run`. Pydantic models with validation. | 3 | **Done 14 Nov 2026** (commit 6719c03): 24 tests; links stored only as TraceLink |
| 1.1b | **Schema extension for H3** (added 14 Nov 2026): process `level` (2, 3, 4) with parent-child links between levels, a `BusinessRule` node (`RUL-001`), and link kinds process → rule and rule → requirement. Graph methods to trace upstream and downstream from any node. **Decided by Linh, 14 Nov 2026:** capabilities are L1; hierarchy is Capability (L1) → L2 → L3 → L4 activity → steps; steps belong to L4 activities only (`PRC-012.3` = step 3 of L4 activity `PRC-012`); one business rule can apply to several processes (many-to-many links). | 2 | **Done 17 Nov 2026**: 37 schema tests; one parent per process; forward/backward tracing |
| 1.2 | **ID rules + canonicaliser v0** (`canonicalise.py`): ID formats `CAP-001`, `PRC-003`, `PRC-003.2`, `RUL-001`, `REQ-F-014`, `REQ-N-003`. Function that renumbers IDs in a deterministic order and normalises whitespace in text (case kept; ignored only for sorting). | 2 | **Done 17 Nov 2026**: scrambled IDs + order → identical output; 46 tests total |
| 1.3 | **Trace store** (`store.py`): SQLite tables `nodes`, `links`, `runs`, `llm_calls`. Functions: `add_node`, `add_link`, `get_nodes(type, run)`, `get_chain(req_id)` (requirement → process → capability → problem), `export_graph(run)`. | 3 | A hand-made mini case round-trips: write → read → identical |
| 1.4 | **LLM wrapper** (`llm.py`): one `call()` function over the Claude API. It logs model, prompt hash, temperature, tokens in/out, latency, cost and run ID into `llm_calls`, and supports structured output into a Pydantic schema. Provider is a setting so OpenAI can be added later. | 3 | A test call is logged with tokens and cost; a mocked test runs without a key |
| 1.5 | **Mini fixture**: a tiny made-up case (one problem, 2 capabilities, an L2 → L3 → L4 chain, 2 rules, 6 requirements) in `tests/fixtures/` for the tests above. | 1 | Used by tests 1.2 and 1.3 |

---

## Phase 2 — Gold standards + scoring harness (23 Nov – 20 Dec)

### 2A. Gold-standard cases

Write the **acceptance rules first**, then the gold standard, then leave it for at least a week before re-reviewing (see the bias note in BUILD_PLAN §5).

| # | Task | Hrs | Done when |
|---|---|---|---|
| 2.1 | **Gold format** (`benchmarks/FORMAT.md`) and a validator that checks every gold file loads into the schemas and every link points to a real ID. | 1.5 | Validator passes on the mini fixture |
| 2.2 | **Insurance claims finance** (benchmark domain). Synthetic, type of problem only, no WCQ content. Aim for: problem ~1–2 pages, ~6–10 capabilities, ~10–15 processes across L2–L4, ~8–15 business rules, ~40–60 requirements. | 6 | Validator passes; `NOTES.md` has acceptance rules + build date |
| 2.3 | **App product development** (transfer A), similar size, with L2–L4 processes and rules. Commit it, then don't open it during tuning. | 4.5 | As above |
| 2.4 | **Small retail** (transfer B), similar size, with L2–L4 processes and rules. Same rule. | 4.5 | As above |

**Gold file example** (`gold/requirements.yaml`):

```yaml
- id: REQ-F-001
  kind: functional
  statement: The system shall record each claim payment against its claim number.
  source_process: PRC-002
  must_have: true        # counts toward coverage
- id: REQ-N-001
  kind: non_functional
  statement: Payment records shall be retained for 7 years.
  source_process: PRC-002
  must_have: false       # nice-to-have; reported separately
```

### 2B. Scoring harness

The tricky part: the engine will never word a requirement exactly the way the gold standard does, so scoring needs a **matching step**.

**Decision (confirmed 4 Nov 2026):** use an LLM judge with a fixed prompt at temperature 0. It decides, for each generated requirement, which gold requirement (if any) it matches. Linh spot-checks 20% of judge decisions on the baseline run, and the agreement rate is recorded. If agreement is below 90%, change the judge prompt before trusting any scores. That agreement figure is part of the evidence the ruler is reliable.

| # | Task | Hrs | Done when |
|---|---|---|---|
| 2.5 | **Matcher** (`eval/match.py`): LLM-judge matching, generated → gold, at most one match per gold item. Cache judge results so re-scoring is free. | 2 | Works on the mini fixture |
| 2.6 | **Metrics** (`eval/metrics.py`): coverage (must-have gold matched / must-have gold), invalid/duplicate rate, link precision/recall (a link is correct if both ends match gold items that are linked in gold), orphan rate, tokens per stage, latency, $ per run, run-to-run agreement (Jaccard over matched gold IDs and links). | 2.5 | Unit tests with hand-computed answers |
| 2.7 | **`mamo score <run_id> --case <case>`** CLI that writes `runs/<run_id>/score.json` + a short `score.md` table. | 1 | Produces a report for a fake run |

---

## Phase 3 — Baseline, MAMO-RT-01 (14–31 Dec 2026)

| # | Task | Hrs | Done when |
|---|---|---|---|
| 3.1 | **Baseline agent** (`src/mamo/baseline.py`): one prompt, problem text → capabilities, processes, requirements and links in one structured output. Written into the store like any other run. | 1.5 | One run completes on the insurance case |
| 3.2 | **Runs**: 5 runs × 3 cases = 15 runs at the default settings. Unlock transfer gold only for scoring. | 1 | 15 scored runs |
| 3.3 | **Judge spot-check**: Linh reviews 20% of match decisions and records the agreement rate. | 1.5 | Agreement % logged |
| 3.4 | **Log + report**: `experiments/MAMO-RT-01.md` with metrics per case, mean and spread over the 5 runs, observed failure types, and what that means for the Phase 4 design. | 2 | Committed and pushed; timesheet hours attached |

**Expected API cost for Phase 3:** small, roughly AUD 10–40 for 15 runs plus judging, depending on model and case size. The wrapper's cost log will give the real figure.

---

## Decisions you'll make during this stretch

| When | Decision | Default if you don't decide |
|---|---|---|
| 0.2 | Do any prior-knowledge findings narrow H1–H5? | Keep H1–H5 as is |
| 1.4 | Which Claude model for engine runs vs the judge | Same mid-tier model for both; record the model ID in every run |
| 2B | ~~Accept LLM-judge matching (with spot-checks)~~ | Confirmed 4 Nov 2026 |
| 3.4 | Is the baseline already near target? If so, the benchmark may be too easy | Re-review the gold standards before Phase 4 |

---

## Weekly rhythm (about 5 hrs)

1. **Start (5 min):** pick the next task #, open a branch if it's experimental.
2. **Work (≈4.5 hrs)** in one or two blocks.
3. **End (10 min):** commit with a clear message, push, fill in the timesheet row (task #, hours, R&D type).

## Logging your own time

Thinking and planning time counts as R&D when it's spent on these tasks: for example working through the trace-store design on a walk, or sketching gold-standard processes on paper. It only holds up if it's recorded **on the day**, with enough detail to show what it was:

- Log it the same day in the timesheet with mode = *own work*.
- Write one line on what you worked out (for example "decided link-matching rule: both endpoints must match linked gold items").
- If it produced a sketch or notes, photograph or save them to `research/notes/YYYY-MM-DD_<topic>.md` and commit. That gives the hours a dated trace.
- Don't log time on WCQ/FCM delivery, admin or general reading unrelated to a task #.

A timesheet line with no task # and no "what was worked out" is the kind an assessor is likely to question.

---

**Handoff:** Plan approved (capacity (a), LLM-judge matching). Frontier team starts tasks 0.1–0.3 this week.
