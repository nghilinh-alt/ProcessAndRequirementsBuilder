# MAMO Engine — Detailed build plan, Phases 0–3 (Nov 2026 – Jan 2027)

**Prepared:** 4 Nov 2026 · **Status:** Approved by Linh Nghi, 4 Nov 2026
**Parent plan:** [BUILD_PLAN.md](BUILD_PLAN.md)
**Capacity:** ~6 hrs/week to 31 Dec 2026 (option (a), confirmed 4 Nov 2026). This includes Linh's own design and planning time away from the keyboard, not just sessions with Claude.

This plan covers everything up to and including the **single-agent baseline (MAMO-RT-01)**. That baseline is the yardstick every later experiment is measured against, so these phases are about building a reliable ruler, not a clever engine.

---

## 0. Summary

| Phase | What you end up with | Est. hours | Target finish | R&D type |
|---|---|---|---|---|
| 0 | Timesheet, prior-knowledge search, Python project skeleton | 6 | 8 Nov | Supporting / admin |
| 1 | Schemas, ID rules, SQLite trace store, logged LLM wrapper | 12 | 29 Nov | Supporting |
| 2 | 3 gold-standard cases + scoring harness | 19 | 20 Dec | Supporting |
| 3 | Baseline runs, scored report, MAMO-RT-01 log | 6 | 31 Dec 2026 | **Core** |
| | **Total** | **~43** | | |

**Capacity (decided 4 Nov 2026):** option (a), ~6 hrs/week, so the baseline lands by **31 Dec 2026**. The hours count all R&D work on these tasks, including Linh's own thinking, sketching and planning done outside Claude sessions, as long as it's logged (see "Logging your own time" below).

The claim starts in **Nov 2026**; Aug–Oct 2026 work is not claimed (decided 4 Nov 2026). Phases 0–3 need ~43 hrs, leaving ~5 hrs of slack in the ~48 available at 6 hrs/week. At Linh's $70/hr rate, the FY26-27 $30k budget needs ~329 director hrs, so ~286 in Jan–Jun 2027 (**~11 hrs/week**). The $20k eligibility floor needs ~186 hrs, so ~143 in Jan–Jun (**~5.5 hrs/week**). The R&D plan §5.1 has the breakdown. Phase 4–7 plans will be sized to real experimental work, not to the dollar target.

## Week-by-week schedule (start Wed 4 Nov 2026)

| Week | Tasks | Hrs |
|---|---|---|
| 4–8 Nov | 0.1 timesheet (today), 0.2 prior-knowledge search, 0.3 Python skeleton → **Phase 0 done** | 6 |
| 9–15 Nov | 1.1 schemas, 1.2 ID rules + canonicaliser | 5 |
| 16–22 Nov | 1.3 trace store, 1.4 LLM wrapper | 6 |
| 23–29 Nov | 1.5 mini fixture → **Phase 1 done**; 2.1 gold format; start 2.2 insurance case | 6 |
| 30 Nov–6 Dec | Finish 2.2; 2.3 app-dev case | 5 |
| 7–13 Dec | 2.4 retail case; 2.5 matcher | 5.5 |
| 14–20 Dec | Re-review insurance gold (≥1 week gap); 2.6 metrics, 2.7 score CLI → **Phase 2 done**; 3.1 baseline agent | 5 |
| 21–27 Dec | Re-review transfer gold; 3.2 baseline runs; 3.3 judge spot-check (light week) | 2.5 |
| 28–31 Dec | 3.4 MAMO-RT-01 log → **Phase 3 done** | 2 |
| | **Total** (≈5 hrs spare in the ~48 available, for slippage) | **43** |

Christmas weeks are planned light on purpose. If an earlier week slips, use the spare there first, then let 3.4 move to the first days of Jan 2027.

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
| 1.1 | **Schemas** (`src/mamo/schemas.py`): `Problem`, `Capability`, `Process`, `Step`, `Requirement`, `TraceLink`, `Run`. Pydantic models with validation (for example a requirement must have a statement and a parent process). | 3 | Unit tests for valid and invalid objects |
| 1.2 | **ID rules + canonicaliser v0** (`canonicalise.py`): ID formats `CAP-001`, `PRC-003`, `PRC-003.2`, `REQ-F-014`, `REQ-N-003`. Function that renumbers IDs in a deterministic order and normalises whitespace and casing in statements. | 2 | Same input graph → same IDs every time (test) |
| 1.3 | **Trace store** (`store.py`): SQLite tables `nodes`, `links`, `runs`, `llm_calls`. Functions: `add_node`, `add_link`, `get_nodes(type, run)`, `get_chain(req_id)` (requirement → process → capability → problem), `export_graph(run)`. | 3 | A hand-made mini case round-trips: write → read → identical |
| 1.4 | **LLM wrapper** (`llm.py`): one `call()` function over the Claude API. It logs model, prompt hash, temperature, tokens in/out, latency, cost and run ID into `llm_calls`, and supports structured output into a Pydantic schema. Provider is a setting so OpenAI can be added later. | 3 | A test call is logged with tokens and cost; a mocked test runs without a key |
| 1.5 | **Mini fixture**: a tiny made-up case (one problem, 2 capabilities, 3 processes, 6 requirements) in `tests/fixtures/` for the tests above. | 1 | Used by tests 1.2 and 1.3 |

---

## Phase 2 — Gold standards + scoring harness (23 Nov – 20 Dec)

### 2A. Gold-standard cases

Write the **acceptance rules first**, then the gold standard, then leave it for at least a week before re-reviewing (see the bias note in BUILD_PLAN §5).

| # | Task | Hrs | Done when |
|---|---|---|---|
| 2.1 | **Gold format** (`benchmarks/FORMAT.md`) and a validator that checks every gold file loads into the schemas and every link points to a real ID. | 1.5 | Validator passes on the mini fixture |
| 2.2 | **Insurance claims finance** (benchmark domain). Synthetic, type of problem only, no WCQ content. Aim for: problem ~1–2 pages, ~6–10 capabilities, ~10–15 processes, ~40–60 requirements. | 5 | Validator passes; `NOTES.md` has acceptance rules + build date |
| 2.3 | **App product development** (transfer A), similar size. Commit it, then don't open it during tuning. | 3.5 | As above |
| 2.4 | **Small retail** (transfer B), similar size. Same rule. | 3.5 | As above |

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
