"""Typed artefacts for the MAMO trace graph (task 1.1).

Design rule: parent/child relationships live only in TraceLink objects.
Nodes never store their parent IDs, so there is one source of truth for
links, which is what H2 measures. Orphans (nodes with no upstream link)
are allowed and reported by TraceGraph.orphans(); they are a measured
outcome, not a validation error.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# ---------------------------------------------------------------------------
# ID formats (canonical renumbering is task 1.2; here we only check the shape)
# ---------------------------------------------------------------------------
PROBLEM_ID = r"^PRB-\d{3}$"
CAPABILITY_ID = r"^CAP-\d{3}$"
PROCESS_ID = r"^PRC-\d{3}$"
STEP_ID = r"^PRC-\d{3}\.\d+$"
REQUIREMENT_ID = r"^REQ-[FN]-\d{3}$"

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
    id: Annotated[str, Field(pattern=PROCESS_ID)]
    name: NonEmpty
    description: str = ""
    actors: list[NonEmpty] = []
    inputs: list[NonEmpty] = []
    outputs: list[NonEmpty] = []


class Step(_Base):
    """A step inside a process. Its parent is fixed by its ID: PRC-003.2 is step 2 of PRC-003."""

    id: Annotated[str, Field(pattern=STEP_ID)]
    description: NonEmpty
    actor: str = ""

    @property
    def process_id(self) -> str:
        return self.id.split(".")[0]


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
    PROCESS_REQUIREMENT = "process_requirement"  # from a Process or one of its Steps


# Allowed (from-node type, to-node type) for each link kind.
_LINK_ENDPOINTS: dict[LinkKind, tuple[tuple[type, ...], type]] = {
    LinkKind.PROBLEM_CAPABILITY: ((Problem,), Capability),
    LinkKind.CAPABILITY_PROCESS: ((Capability,), Process),
    LinkKind.PROCESS_REQUIREMENT: ((Process, Step), Requirement),
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
    temperature: float = Field(ge=0.0)
    seed: int | None = None
    config_hash: str = ""
    notes: str = ""


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
Node = Problem | Capability | Process | Step | Requirement


class TraceGraph(_Base):
    """All nodes and links for one run (or one gold standard, with run_id=None)."""

    run_id: str | None = None
    problems: list[Problem] = []
    capabilities: list[Capability] = []
    processes: list[Process] = []
    steps: list[Step] = []
    requirements: list[Requirement] = []
    links: list[TraceLink] = []

    def nodes(self) -> dict[str, Node]:
        out: dict[str, Node] = {}
        for group in (self.problems, self.capabilities, self.processes, self.steps, self.requirements):
            for node in group:
                out[node.id] = node
        return out

    @model_validator(mode="after")
    def _check_integrity(self) -> TraceGraph:
        all_ids = [
            n.id
            for g in (self.problems, self.capabilities, self.processes, self.steps, self.requirements)
            for n in g
        ]
        dupes = sorted({i for i in all_ids if all_ids.count(i) > 1})
        if dupes:
            raise ValueError(f"duplicate node IDs: {dupes}")

        nodes = self.nodes()
        process_ids = {p.id for p in self.processes}
        missing_parents = sorted(s.id for s in self.steps if s.process_id not in process_ids)
        if missing_parents:
            raise ValueError(f"steps whose process is missing: {missing_parents}")

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
        return self

    def orphans(self) -> list[str]:
        """Capabilities, processes and requirements with no upstream link, sorted.

        Steps are excluded: their parent is fixed by their ID.
        """
        has_parent = {link.to_id for link in self.links}
        candidates = [*self.capabilities, *self.processes, *self.requirements]
        return sorted(n.id for n in candidates if n.id not in has_parent)
