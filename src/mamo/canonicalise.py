"""Canonical IDs and text for a trace graph (task 1.2).

The engine (or the LLM inside it) hands out IDs in whatever order it likes.
canonicalise() renumbers every node from its content and its place in the
hierarchy, so the same graph always comes out with the same IDs. That is what
makes runs comparable for repeatability (H4) and scoring.

Ordering:
- Problems: by position in the source text, then kind, then text.
- Capabilities: by name.
- Processes: tree order. Each capability in turn, then its L2s, L3s and L4s,
  by name at each level. Processes with no parent come last, by level then name.
- Steps: keep their order inside each L4 activity; renumbered 1, 2, 3...
- Rules and requirements: by the earliest process, step or rule they hang off,
  then by statement. Unlinked ones come last. Functional and non-functional
  requirements are numbered separately (REQ-F-001..., REQ-N-001...).

Text: repeated spaces and line breaks are collapsed to one space. Case is kept;
it is ignored only for sorting. Ties left after all of this (two siblings with
the same name) fall back to the incoming ID.
"""

from __future__ import annotations

import re

from mamo.schemas import (
    LinkKind,
    Requirement,
    RequirementKind,
    TraceGraph,
)

_SPACES = re.compile(r"\s+")
_TEXT_FIELDS = ("text", "name", "description", "statement", "rationale", "actor")
_LINK_ORDER = list(LinkKind)


def _clean(text: str) -> str:
    return _SPACES.sub(" ", text).strip()


def _key(text: str) -> str:
    return _clean(text).casefold()


def canonicalise(graph: TraceGraph) -> tuple[TraceGraph, dict[str, str]]:
    """Return the canonical graph and the mapping old ID -> new ID."""
    mapping: dict[str, str] = {}

    # Problems
    def problem_key(p):
        start = p.source.start if p.source else float("inf")
        return (start, p.kind.value, _key(p.text), p.id)

    for i, p in enumerate(sorted(graph.problems, key=problem_key), 1):
        mapping[p.id] = f"PRB-{i:03d}"

    # Capabilities
    caps = sorted(graph.capabilities, key=lambda c: (_key(c.name), c.id))
    for i, c in enumerate(caps, 1):
        mapping[c.id] = f"CAP-{i:03d}"

    # Processes in tree order
    procs = {p.id: p for p in graph.processes}
    children: dict[str, list[str]] = {}
    for link in graph.links:
        if link.kind in (LinkKind.CAPABILITY_PROCESS, LinkKind.PROCESS_PROCESS):
            children.setdefault(link.from_id, []).append(link.to_id)

    order: list[str] = []

    def visit(parent_id: str) -> None:
        kids = sorted(children.get(parent_id, []), key=lambda pid: (_key(procs[pid].name), pid))
        for pid in kids:
            order.append(pid)
            visit(pid)

    for c in caps:
        visit(c.id)
    # Processes with no parent (and anything under them) last, by level then name
    has_parent = {kid for kids in children.values() for kid in kids}
    for p in sorted(procs.values(), key=lambda p: (p.level, _key(p.name), p.id)):
        if p.id not in has_parent:
            order.append(p.id)
            visit(p.id)
    for i, pid in enumerate(order, 1):
        mapping[pid] = f"PRC-{i:03d}"

    # Steps keep their sequence inside each L4 activity
    def step_no(step_id: str) -> int:
        return int(step_id.split(".")[1])

    steps_by_parent: dict[str, list] = {}
    for s in graph.steps:
        steps_by_parent.setdefault(s.process_id, []).append(s)
    for parent, steps in steps_by_parent.items():
        for i, s in enumerate(sorted(steps, key=lambda s: (step_no(s.id), s.id)), 1):
            mapping[s.id] = f"{mapping[parent]}.{i}"

    # Position of every process and step in the tree, for ordering rules and requirements
    position: dict[str, tuple] = {}
    for i, pid in enumerate(order):
        position[pid] = (i, 0)
        for s in steps_by_parent.get(pid, []):
            position[s.id] = (i, int(mapping[s.id].split(".")[1]))

    parents_of: dict[str, list[str]] = {}
    for link in graph.links:
        parents_of.setdefault(link.to_id, []).append(link.from_id)

    unlinked = (float("inf"),)

    def earliest(node_id: str) -> tuple:
        found = [position[p] for p in parents_of.get(node_id, []) if p in position]
        return min(found) if found else unlinked

    rules = sorted(graph.rules, key=lambda r: (earliest(r.id), _key(r.statement), r.id))
    for i, r in enumerate(rules, 1):
        mapping[r.id] = f"RUL-{i:03d}"
        position[r.id] = (*earliest(r.id), 1, i)  # just after the process or step it hangs off

    def req_key(r: Requirement) -> tuple:
        return (earliest(r.id), _key(r.statement), r.id)

    for kind, prefix in ((RequirementKind.FUNCTIONAL, "REQ-F"), (RequirementKind.NON_FUNCTIONAL, "REQ-N")):
        reqs = sorted((r for r in graph.requirements if r.kind == kind), key=req_key)
        for i, r in enumerate(reqs, 1):
            mapping[r.id] = f"{prefix}-{i:03d}"

    # Rebuild with new IDs and cleaned text
    def rebuild(nodes: list) -> list:
        out = []
        for n in nodes:
            data = n.model_dump()
            data["id"] = mapping[n.id]
            for field in _TEXT_FIELDS:
                if isinstance(data.get(field), str):
                    data[field] = _clean(data[field])
            for field in ("actors", "inputs", "outputs", "acceptance"):
                if field in data:
                    data[field] = [_clean(x) for x in data[field]]
            out.append(type(n).model_validate(data))
        return sorted(out, key=lambda n: n.id)

    links = []
    for link in graph.links:
        data = link.model_dump()
        data["from_id"], data["to_id"] = mapping[link.from_id], mapping[link.to_id]
        data["verifier_note"] = _clean(data["verifier_note"])
        links.append(data)
    links.sort(key=lambda d: (_LINK_ORDER.index(LinkKind(d["kind"])), d["from_id"], d["to_id"]))

    canonical = TraceGraph(
        run_id=graph.run_id,
        problems=rebuild(graph.problems),
        capabilities=rebuild(graph.capabilities),
        processes=rebuild(graph.processes),
        steps=rebuild(graph.steps),
        rules=rebuild(graph.rules),
        requirements=rebuild(graph.requirements),
        links=links,
    )
    return canonical, mapping
