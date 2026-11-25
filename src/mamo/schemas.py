"""Typed artefacts for the MAMO trace graph (tasks 1.1 and 1.1b).

Hierarchy (decided by Linh, 14 Nov 2026):
    Problem -> Capability (L1) -> L2 process -> L3 process -> L4 activity -> steps
Business rules hang off processes or steps and can apply to several of them.
Requirements hang off a process, a step or a rule.
Each process has exactly one parent (a capability for L2, the level above otherwise).

Design rule: parent/child relationships live only in TraceLink objects.
Nodes never store their parent IDs, so there is one source of truth for
links, which is what H2 measures. Orphans (nodes with no upstream link)
are allowed and reported by TraceGraph.orphans(); they are a measured
outcome, not a validation error.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# ---------------------------------------------------------------------------
# ID formats (canonical renumbering is task 1.2; here we only check the shape)
# ---------------------------------------------------------------------------
PROBLEM_ID = r"^PRB-\d{3}$"
CAPABILITY_ID = r"^CAP-\d{3}$"
PROCESS_ID = r"^PRC-\d{3}$"
STEP_ID = r"^PRC-\d{3}\.\d+$"
REQUIREMENT_ID = r"^REQ-[FN]-\d{3}$"
RULE_ID = r"^RUL-\d{3}$"

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SourceSpan(_Base):
    """Character range in the original problem text that a node came from."""

    start: int = Field(ge=0)
    end: int

    @model_validator(mode="after")
    def _end_after_start(self) -> SourceSpan:
        if self.end <= self.start:
            raise ValueError("end must be greater than start")
        return self


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
class ProblemKind(str, Enum):
    STATEMENT = "statement"
    ACTOR = "actor"
    GOAL = "goal"
    CONSTRAINT = "constraint"
    PAIN_POINT = "pain_point"


class Problem(_Base):
    id: Annotated[str, Field(pattern=PROBLEM_ID)]
    kind: ProblemKind
    text: NonEmpty
    source: SourceSpan | None = None


class Capability(_Base):
    id: Annotated[str, Field(pattern=CAPABILITY_ID)]
    name: NonEmpty
    description: str = ""


class Process(_Base):
    """An L2 process, L3 process or L4 activity."""

    id: Annotated[str, Field(pattern=PROCESS_ID)]
    level: Literal[2, 3, 4]
    name: NonEmpty
    description: str = ""
    actors: list[NonEmpty] = []
    inputs: list[NonEmpty] = []
    outputs: list[NonEmpty] = []


class Step(_Base):
    """A step inside an L4 activity. Its parent is fixed by its ID: PRC-003.2 is step 2 of PRC-003."""

    id: Annotated[str, Field(pattern=STEP_ID)]
    description: NonEmpty
    actor: str = ""

    @property
    def process_id(self) -> str:
        return self.id.split(".")[0]


class BusinessRule(_Base):
    id: Annotated[str, Field(pattern=RULE_ID)]
    statement: NonEmpty
    rationale: str = ""
    source: SourceSpan | None = None


class RequirementKind(str, Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"


class Requirement(_Base):
    id: Annotated[str, Field(pattern=REQUIREMENT_ID)]
    kind: RequirementKind
    statement: NonEmpty
    acceptance: list[NonEmpty] = []
    rationale: str = ""
    must_have: bool = True

    @model_validator(mode="after")
    def _kind_matches_id(self) -> Requirement:
        expected = (
            RequirementKind.FUNCTIONAL if self.id.startswith("REQ-F-") else RequirementKind.NON_FUNCTIONAL
        )
        if self.kind != expected:
            raise ValueError(f"{self.id} has kind {self.kind.value}, but its ID says {expected.value}")
        return self


# ---------------------------------------------------------------------------
# Links and runs
# ---------------------------------------------------------------------------
class LinkKind(str, Enum):
    PROBLEM_CAPABILITY = "problem_capability"
    CAPABILITY_PROCESS = "capability_process"
    PROCESS_PROCESS = "process_process"  # parent level -> child level + 1
    PROCESS_RULE = "process_rule"  # from a Process or Step; a rule may have many
    PROCESS_REQUIREMENT = "process_requirement"  # from a Process or one of its Steps
    RULE_REQUIREMENT = "rule_requirement"


# Allowed (from-node type, to-node type) for each link kind.
_LINK_ENDPOINTS: dict[LinkKind, tuple[tuple[type, ...], type]] = {
    LinkKind.PROBLEM_CAPABILITY: ((Problem,), Capability),
    LinkKind.CAPABILITY_PROCESS: ((Capability,), Process),
    LinkKind.PROCESS_PROCESS: ((Process,), Process),
    LinkKind.PROCESS_RULE: ((Process, Step), BusinessRule),
    LinkKind.PROCESS_REQUIREMENT: ((Process, Step), Requirement),
    LinkKind.RULE_REQUIREMENT: ((BusinessRule,), Requirement),
}


class TraceLink(_Base):
    from_id: NonEmpty
    to_id: NonEmpty
    kind: LinkKind
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    verified: bool | None = None  # None = not yet checked by the verifier
    verifier_note: str = ""

    @model_validator(mode="after")
    def _not_self(self) -> TraceLink:
        if self.from_id == self.to_id:
            raise ValueError("a link cannot point to itself")
        return self


class Run(_Base):
    """One execution of the engine (or the baseline) on one case."""

    id: NonEmpty
    case: NonEmpty
    started_at: datetime
    model: NonEmpty
    effort: Literal["low", "medium", "high", "xhigh", "max"] | None = None  # None = API default
    seed: int | None = None  # only for our own randomness (e.g. sampling); the API has no seed
    config_hash: str = ""
    notes: str = ""


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
Node = Problem | Capability | Process | Step | BusinessRule | Requirement


class TraceGraph(_Base):
    """All nodes and links for one run (or one gold standard, with run_id=None)."""

    run_id: str | None = None
    problems: list[Problem] = []
    capabilities: list[Capability] = []
    processes: list[Process] = []
    steps: list[Step] = []
    rules: list[BusinessRule] = []
    requirements: list[Requirement] = []
    links: list[TraceLink] = []

    def _groups(self) -> tuple[list, ...]:
        return (self.problems, self.capabilities, self.processes, self.steps, self.rules, self.requirements)

    def nodes(self) -> dict[str, Node]:
        return {node.id: node for group in self._groups() for node in group}

    @model_validator(mode="after")
    def _check_integrity(self) -> TraceGraph:
        all_ids = [n.id for g in self._groups() for n in g]
        dupes = sorted({i for i in all_ids if all_ids.count(i) > 1})
        if dupes:
            raise ValueError(f"duplicate node IDs: {dupes}")

        nodes = self.nodes()
        levels = {p.id: p.level for p in self.processes}
        missing_parents = sorted(s.id for s in self.steps if s.process_id not in levels)
        if missing_parents:
            raise ValueError(f"steps whose process is missing: {missing_parents}")
        not_l4 = sorted(s.id for s in self.steps if levels[s.process_id] != 4)
        if not_l4:
            raise ValueError(f"steps must belong to an L4 activity: {not_l4}")

        seen: set[tuple[str, str]] = set()
        for link in self.links:
            for end in (link.from_id, link.to_id):
                if end not in nodes:
                    raise ValueError(f"link {link.from_id} -> {link.to_id} points to unknown node {end}")
            from_types, to_type = _LINK_ENDPOINTS[link.kind]
            if not isinstance(nodes[link.from_id], from_types) or not isinstance(nodes[link.to_id], to_type):
                # ValueError, not TypeError: pydantic only reports ValueError as a validation error
                raise ValueError(f"link {link.from_id} -> {link.to_id} doesn't fit kind {link.kind.value}")  # noqa: TRY004
            pair = (link.from_id, link.to_id)
            if pair in seen:
                raise ValueError(f"duplicate link {link.from_id} -> {link.to_id}")
            seen.add(pair)

            if link.kind is LinkKind.CAPABILITY_PROCESS and levels[link.to_id] != 2:
                raise ValueError(f"capability {link.from_id} must link to an L2 process, not {link.to_id}")
            if link.kind is LinkKind.PROCESS_PROCESS and levels[link.to_id] != levels[link.from_id] + 1:
                raise ValueError(
                    f"{link.from_id} (L{levels[link.from_id]}) -> {link.to_id} (L{levels[link.to_id]}) "
                    "must go down exactly one level"
                )

        process_parents: dict[str, int] = {}
        for link in self.links:
            if link.kind in (LinkKind.CAPABILITY_PROCESS, LinkKind.PROCESS_PROCESS):
                process_parents[link.to_id] = process_parents.get(link.to_id, 0) + 1
        multi = sorted(pid for pid, n in process_parents.items() if n > 1)
        if multi:
            raise ValueError(f"processes with more than one parent: {multi}")
        return self

    def orphans(self) -> list[str]:
        """Capabilities, processes, rules and requirements with no upstream link, sorted.

        Steps are excluded: their parent is fixed by their ID.
        """
        has_parent = {link.to_id for link in self.links}
        candidates = [*self.capabilities, *self.processes, *self.rules, *self.requirements]
        return sorted(n.id for n in candidates if n.id not in has_parent)

    def _edges(self) -> list[tuple[str, str]]:
        """Parent -> child pairs: every link, plus each L4 activity -> its steps."""
        return [(link.from_id, link.to_id) for link in self.links] + [(s.process_id, s.id) for s in self.steps]

    def _walk(self, start: str, forward: bool) -> list[str]:
        if start not in self.nodes():
            raise KeyError(start)
        nxt: dict[str, list[str]] = {}
        for parent, child in self._edges():
            a, b = (parent, child) if forward else (child, parent)
            nxt.setdefault(a, []).append(b)
        seen: set[str] = set()
        todo = [start]
        while todo:
            for n in nxt.get(todo.pop(), []):
                if n not in seen:
                    seen.add(n)
                    todo.append(n)
        seen.discard(start)
        return sorted(seen)

    def upstream(self, node_id: str) -> list[str]:
        """Everything a node traces back to (backward trace), sorted."""
        return self._walk(node_id, forward=False)

    def downstream(self, node_id: str) -> list[str]:
        """Everything that traces back to a node (forward trace; the basis for H6 impact), sorted."""
        return self._walk(node_id, forward=True)
