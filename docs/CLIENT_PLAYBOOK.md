# Running MAMO on a client engagement

The engine is reused across clients. Client material never enters this repo.

## 1. Set up a separate client workspace

```
rogue-night/client-<name>/      ← separate private repo or local folder
  engine/                        ← MAMO pinned to a tagged release (e.g. v1.0.0)
  inputs/                        ← client problem statements and documents
  outputs/                       ← generated processes, requirements, trace matrix
  domain_pack.yaml               ← optional industry overrides
```

Pin to a release tag so a client's results can be reproduced later.

## 2. Before starting

- [ ] Contract sets out IP: engine = Rogue Night background IP; client owns their deliverables.
- [ ] Client data handling agreed (where it's stored, which model provider, retention).
- [ ] Choose or write a domain pack (glossary, actors, NFR checklist).

## 3. Run

1. Load the problem statement into `inputs/`.
2. Run the pipeline with the default control profile.
3. Review `verification_report.md`. A BA accepts or rejects flagged links.
4. Export the BRD + trace matrix.
5. **Linh reviews before anything goes to the client.**

## 4. Feeding improvements back

If a client job exposes a generic engine weakness, write it up in **generic terms** (no client content), open an issue in the engine repo, and fix it there. Client-specific tweaks stay in the client's domain pack.

## 5. Not R&D

Using the engine on paid client work is commercial work. Log those hours against the client, not against engine experiments.
