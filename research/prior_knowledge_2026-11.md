# Prior-knowledge search — November 2026

**Task:** 0.2 (BUILD_PLAN_P0-3) · R&D plan §3
**Search date:** 4 Nov 2026. Compiled with Claude (web search); **reviewed by Linh Nghi on: ____** (add the date when reviewed and add your own judgement below)
**Purpose:** check whether a competent professional could already know how to do what H1–H5 test, and narrow the hypotheses to what is still unknown.

---

## 1. Summary

No source found does the whole MAMO task: **start from an unstructured business problem, generate capabilities → processes → requirements across several agent stages, and measure whether the generated trace links are correct, repeatable across runs and hold across industries.**

The closest work does one of these instead:
- **Recovers links between artefacts that already exist** (TraceLLM, TVR, Jama, most tools). It doesn't generate the artefacts.
- **Generates requirements but doesn't trace or measure links** (multi-agent elicitation papers, MARE, Copilot4DevOps, Innoslate).
- **Generates downstream with a trace graph** (TraceDev: use cases → design → code). It starts from structured use cases and doesn't measure graph accuracy.

One finding **narrows H3** (see §4): TraceDev already uses a trace graph as compressed agent context, so "a trace graph can reduce tokens" is no longer new on its own.

---

## 2. Academic

| Source | What it does | What it doesn't do (relative to MAMO) |
|---|---|---|
| [TraceLLM](https://arxiv.org/abs/2602.01253) (Alturayeif et al., Feb 2026) | Prompt-engineering framework for trace-link **recovery** between existing requirements, design, tests and regulations. State-of-the-art F2 on 4 datasets, 8 LLMs. | Doesn't generate requirements or processes; no multi-stage generation; no run-to-run repeatability results. |
| [TVR](https://arxiv.org/html/2504.15427v2) (2025) | RAG + LLM **validates and recovers** links between existing automotive stakeholder and system requirements. ~99% validation accuracy, 85.5% recovery correctness. | Single domain (automotive DTCs); existing artefacts only; no generation. |
| [UserTrace](https://arxiv.org/abs/2509.11238v1) (Jin et al., Sep 2025) | 4 agents (Code Reviewer, Searcher, Writer, Verifier) **generate** user-level requirements **from code repositories** and recover links to code. Claims better precision than 5 RT approaches. | Input is existing code, not a business problem; goes code → requirements (reverse direction); repeatability and cross-domain not reported in what was read. |
| [TraceDev](https://arxiv.org/pdf/2607.18886) (Chen et al., ISSTA Oct 2026) | 5 agents turn **structured use cases** into design + code. A Validator agent keeps a directed trace graph (requirement → design → code) and uses it **as compressed context instead of passing full artefacts**. Lower tokens than ChatDev/MetaGPT in most settings. Temperature 0; code released. 2 domains. | Starts from structured use cases, not an unstructured problem; downstream (code), not business processes; **graph accuracy not measured** (authors say so); no run-to-run agreement reported. |
| [AI-based multi-agent elicitation](https://arxiv.org/pdf/2409.00038) (Sami et al., Tampere, 2024) | 4 agents generate, assess and prioritise user stories from a project description. | No traceability; hallucination noted as an open problem; small evaluation (4 projects); generation settings not reported. |
| [MARE](https://www.themoonlight.io/en/review/mare-multi-agents-collaboration-framework-for-requirements-engineering) (review page) | 5 agents for elicitation, modelling, verification and specification. | Trace links not mentioned; evaluation and repeatability not described on the page read. *Read the original paper before relying on this row.* |
| [LLMs for RE: systematic review](https://arxiv.org/html/2509.11446v1) (Sep 2025, 74 studies, 2023–24) | Maps the field. | Tracing appears in only 5 of 74 studies (7%); evaluation is mostly lab experiments; shared datasets are scarce. Supports the gap and the need for a Rogue Night-owned benchmark. |
| [Non-determinism of ChatGPT in code generation](https://arxiv.org/abs/2308.02828v1) (Ouyang et al., 2023; FSE 2025) | Shows large run-to-run variance; **temperature 0 doesn't guarantee determinism**. | Code generation, not requirements. Supports H4: repeatability can't be assumed from settings alone. |

## 3. Commercial tools

| Tool | AI features found | Gap relative to MAMO |
|---|---|---|
| [Jama Connect](https://www.jamasoftware.com/?p=4775) | Live Traceability with "Trace Scores" measuring completeness; document parsing extracts requirements from PDF/Office ([TNW, sponsored](https://thenextweb.com/news/best-ai-requirements-management-software-2026)); an MCP server for AI-assisted development ([Jama blog, Jun 2026](https://www.jamasoftware.com/legacy/blog/2026/06/)). | Traceability completeness is measured over links people create; no evidence found of generating processes, requirements and links from an unstructured problem, or of accuracy/repeatability claims. |
| [IBM Engineering Requirements Management (DOORS Next)](https://www.ibm.com/products/requirements-quality-assistant) | AI quality scoring of requirement wording against standards; natural-language queries, summaries, translation. Partner add-on [requisis ORCA](https://requisis.com/en/produkte/dng-ai-requisis-orca.html) offers a co-pilot. | AI checks quality; traceability is a separate manual linking feature. |
| [Copilot4DevOps (Modern Requirements)](https://www.modernrequirements.com/ai/) | Elicit requirements from raw data; turn business objectives into user stories; generate process diagrams. | No traceability feature described for the AI; no accuracy or repeatability claims. |
| Innoslate, Visure, Codebeamer, Polarion, Valispace ([TNW, sponsored](https://thenextweb.com/news/best-ai-requirements-management-software-2026)) | NLP import to structured requirements (Innoslate); AI quality analysis (Visure); traceability as standard links. | Traceability isn't described as AI-generated or measured for accuracy. |

*Caution: vendor pages and the TNW list are marketing. They show what's claimed, not what's been tested.*

## 4. Open-source

- [TraceDev](https://arxiv.org/pdf/2607.18886) and the Tampere tool release code on GitHub (see §2).
- [contextgit](https://pypi.org/project/contextgit/1.0.3/) (PyPI) and a small [requirements-to-test-agent](https://github.com/hmodali2611/requirements-to-test-agent/issues/1) repo turned up. Neither was checked in depth. *Look at both before the claim is written.*
- Still to do: GitHub issues on crewAI/AutoGen about state drift and context growth (the FY25-26 notes may already cover this; link them here with their dates).

## 5. What this means for H1–H5 (draft, for Linh to decide)

| # | Effect | Suggested change |
|---|---|---|
| H1 | Gap stands. Multi-agent requirement generation exists, but none was measured for coverage against a gold standard from an unstructured problem. | None |
| H2 | Gap stands for **generated** links. Verifier-style agents exist (UserTrace, TraceDev), and recovery between existing artefacts is well studied, but link accuracy across generation stages isn't measured. | Add a note that prior work measures recovery, not generated-link accuracy. Consider comparing the verifier with a TraceLLM-style recovery prompt as an extra baseline. |
| H3 | **Narrowed.** TraceDev already shows a trace graph used as compressed context can lower tokens (downstream, structured input). | Reword so the unknown is: does graph state keep **measured link accuracy** (which TraceDev didn't measure) and coverage for **upstream** generation from unstructured problems, where the graph must be built by the agents themselves rather than from AST parsing? Cite TraceDev in the claim. |
| H4 | Gap stands. Non-determinism at temperature 0 is documented; nothing found on repeatable requirement **sets and IDs**. | None |
| H5 | Gap stands. Sources cover 1–2 domains, not transfer of a frozen pipeline to unseen ones. | None |

## 6. Still to do (part of task 0.2's remaining time)

- [ ] Linh reads TraceDev and UserTrace in full and records her own view here (this is the "competent professional" judgement the claim needs).
- [ ] Read MARE's original paper.
- [ ] Check contextgit and requirements-to-test-agent.
- [ ] Link the FY25-26 searches (crewAI/AutoGen state issues) with their original dates.
- [ ] Optional: ask 1–2 BA/RE practitioners whether a known method exists, and record the date and answer.
