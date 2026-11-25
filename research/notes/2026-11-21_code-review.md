# Code review: tasks 1.1–1.3 (schemas, canonicaliser, trace store)

**Reviewer:** Linh Nghi (BA / director) · **Date:** 21 Nov 2026 · **Planned:** 2 hrs, own work
**Code at commit:** ____ (run `git log --oneline -1` before you start)
**Purpose:** check that the design matches how a BA would model processes, rules and requirements, before the gold standards (Phase 2) are built on it. Changes are much cheaper now than after the test cases exist.

Write your answers under each question. "Fine as is" is a valid answer; say why in a few words.

---

## 1. Hierarchy and structure (`src/mamo/schemas.py`, about 40 min)

Read the docstring at the top, then the `Process`, `Step`, `BusinessRule`, `LinkKind` and `TraceGraph` sections.

1. Capability (L1) → L2 → L3 → L4 activity → steps. Does that match how you map processes in practice? Anything missing (e.g. sub-processes that skip a level, shared L4 activities)?
   -
2. **One parent per process** (an L3 belongs to exactly one L2). Is that right for your work, or do you sometimes reuse an L3/L4 under two parents?
   -
3. Business rules can hang off any process level or a step, and apply to many. Should rules also be able to come straight from the problem (e.g. a regulation stated in the brief)?
   -
4. Requirements can hang off a process, a step or a rule. Is anything missing, e.g. requirements tied to a capability, or one requirement satisfying several processes?
   -
5. Problem item kinds are: statement, actor, goal, constraint, pain point. Any you'd add (e.g. assumption, risk, KPI)?
   -
6. Fields on each item (actors/inputs/outputs on processes, acceptance criteria and must-have on requirements, rationale on rules). Anything a BA deliverable needs that isn't there?
   -

   Fine as is

## 2. Consistent IDs (`src/mamo/canonicalise.py`, about 30 min)

Read the docstring at the top.

7. Processes are numbered in tree order, alphabetically by name within each level. Would you rather the order follow the process sequence (e.g. "Receive claim" before "Assess claim")? If so, how would the engine know the sequence?
   -
8. Steps keep the order they were given. Good, or should steps also be sorted?
   -
9. Requirements are numbered by where they first appear in the tree, functional and non-functional counted separately. Does that suit how you'd present a requirements list?
   -

   Fine as is

## 3. Trace store (`src/mamo/store.py`, about 20 min)

10. Each run is stored separately; gold standards are stored as `gold/<case>`. Anything else you'd need to keep per run (e.g. which prompt version, a note on what was changed)?
    -
11. `get_chain` follows a requirement back to the problem. Is there a second view you'd want as a BA, e.g. "show me every requirement under this L3", or a printable trace matrix?
    -
    Fine as is

## 4. Try it yourself (about 20 min, optional)

In PowerShell with `.venv` active:

```powershell
python -c "from tests.test_schemas import small_graph; from mamo.schemas import TraceGraph; g = TraceGraph.model_validate(small_graph()); print(g.upstream('REQ-F-002')); print(g.downstream('PRC-002'))"
```

If that import fails, run it from the `tests` folder: `cd tests` then `python -c "from test_schemas import small_graph; ..."`.

12. Does the trace output make sense to you? Try changing a level or a link in `tests/test_schemas.py` (`small_graph`) and see what the checks say. Note anything surprising.
    -

Fine as is
---

## Outcome

- **Design changes wanted** (each becomes a task for Claude):
  -
- **Questions for Claude:**
  -
- **Time actually spent:** ___3_ hrs (enter in the timesheet, Mode = Own work, with this file's commit ID)

When done:

```powershell
git add research/notes/2026-11-21_code-review.md
git commit -m "Code review 1.1-1.3: findings"
git push
```
