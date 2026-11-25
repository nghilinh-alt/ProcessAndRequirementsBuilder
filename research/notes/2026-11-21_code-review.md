# Code review: tasks 1.1–1.3 (schemas, canonicaliser, trace store)

**Reviewer:** Linh Nghi (BA / director) · **Review date:** 25 Nov 2026 (planned for 21 Nov) · **Planned:** 2 hrs, own work
**Code at commit:** 07f7b3c
**Purpose:** check that the design matches how a BA would model processes, rules and requirements, before the gold standards (Phase 2) are built on it.

**How to read this file:** *Linh's answer* is Linh's decision. *Design reasoning (Claude)* explains why the code is built that way; it was written by Claude when tidying this file on 25 Nov and is not Linh's own wording. *Linh's reason* is for Linh's own one-line justification.

**Overall result:** no design changes. Linh accepted the design of 1.1–1.3 as built.

---

## 1. Hierarchy and structure (`src/mamo/schemas.py`)

**1. Capability (L1) → L2 → L3 → L4 activity → steps. Does that match how you map processes? Anything missing?**
- Linh's answer: matches the hierarchy set on 14 Nov. Skipping a level is rejected so every requirement has a complete chain back to its capability, which H3 measures.
- 

**2. One parent per process (an L3 belongs to exactly one L2). Right for your work?**
- Linh's answer: a strict tree keeps each process's backward trace unambiguous. If an activity appears under two L3s, it is modelled as two L4s. Easy to relax later if a gold case needs shared processes.
-

**3. Should business rules also be able to come straight from the problem (e.g. a regulation in the brief)?**
- Linh's answer: a rule stated in the brief is still traced to its source and linked to the processes it governs. 


**4. Requirements can hang off a process, a step or a rule. Anything missing?**
- Linh's answer: one requirement may already link to several processes, steps or rules (links aren't limited to one parent for requirements). Capability-level requirements are left out to keep requirements tied to something testable.


**5. Problem item kinds: statement, actor, goal, constraint, pain point. Any to add (assumption, risk, KPI)?**
- Linh's answer: the five kinds cover what the intake agent extracts from a brief. More kinds can be added.
- 

**6. Fields on each item. Anything a BA deliverable needs that isn't there?**
- Linh's answer: fields are the minimum needed to score coverage and links. 

## 2. Consistent IDs (`src/mamo/canonicalise.py`)

**7. Processes numbered in tree order, alphabetically within each level. Prefer business sequence?**
- Linh's answer: alphabetical order needs nothing the engine can get wrong, so IDs stay repeatable.

**8. Steps keep the order they were given. Good?**
- Linh's answer: step order carries meaning inside an L4 activity, so it is kept and only renumbered 1, 2, 3.


**9. Requirements numbered by first appearance in the tree, F and N counted separately. Suits how you'd present them?**
- Linh's answer: groups requirements under the part of the process they come from, which is how a trace matrix reads.


## 3. Trace store (`src/mamo/store.py`)

**10. Anything else to keep per run (prompt version, change note)?**
- Linh's answer: each run already records model, temperature, seed, config hash and notes; prompt versions will be covered by the config hash once prompts exist (Phase 3–4).


**11. A second BA view, e.g. every requirement under an L3, or a printable trace matrix?**
- Linh's answer: Not needed.

## 4. Try it yourself

**12. Does the trace output make sense?**
- Linh's answer: Yes it does.

---

## Outcome

- **Design changes wanted:** none.
- **Questions for Claude:** none.
- **Time actually spent:** ____ hrs, on ____ (date or dates). Enter the same in timesheet row 26 with this file's commit ID.

When done:

```powershell
git add research/notes/2026-11-21_code-review.md
git commit -m "Code review 1.1-1.3: findings"
git push
```
