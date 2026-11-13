from datetime import datetime

import pytest
from pydantic import ValidationError

from mamo.schemas import (
    Capability,
    LinkKind,
    Problem,
    Process,
    Requirement,
    Run,
    SourceSpan,
    Step,
    TraceGraph,
    TraceLink,
)


def small_graph(**overrides) -> dict:
    """A tiny valid graph as plain data: 1 problem, 1 capability, 1 process with 1 step, 2 requirements."""
    data = {
        "problems": [{"id": "PRB-001", "kind": "pain_point", "text": "Claim payments are reconciled by hand.",
                      "source": {"start": 0, "end": 38}}],
        "capabilities": [{"id": "CAP-001", "name": "Payment reconciliation"}],
        "processes": [{"id": "PRC-001", "name": "Reconcile claim payments", "actors": ["Finance officer"]}],
        "steps": [{"id": "PRC-001.1", "description": "Match payment to claim number", "actor": "Finance officer"}],
        "requirements": [
            {"id": "REQ-F-001", "kind": "functional",
             "statement": "The system shall match each payment to its claim number."},
            {"id": "REQ-N-001", "kind": "non_functional",
             "statement": "Payment records shall be retained for 7 years.", "must_have": False},
        ],
        "links": [
            {"from_id": "PRB-001", "to_id": "CAP-001", "kind": "problem_capability"},
            {"from_id": "CAP-001", "to_id": "PRC-001", "kind": "capability_process"},
            {"from_id": "PRC-001.1", "to_id": "REQ-F-001", "kind": "process_requirement", "confidence": 0.9},
            {"from_id": "PRC-001", "to_id": "REQ-N-001", "kind": "process_requirement"},
        ],
    }
    data.update(overrides)
    return data


# --- valid objects ---------------------------------------------------------

def test_valid_graph_loads_and_has_no_orphans():
    g = TraceGraph.model_validate(small_graph())
    assert len(g.nodes()) == 6
    assert g.orphans() == []


def test_graph_round_trips_through_json():
    g = TraceGraph.model_validate(small_graph())
    assert TraceGraph.model_validate_json(g.model_dump_json()) == g


def test_step_knows_its_process():
    assert Step(id="PRC-012.3", description="Approve").process_id == "PRC-012"


def test_whitespace_is_stripped():
    c = Capability(id="CAP-002", name="  Reporting  ")
    assert c.name == "Reporting"


def test_run_record():
    r = Run(id="run-001", case="insurance_claims_finance", started_at=datetime(2026, 12, 22, 10, 0),
            model="claude-x", temperature=0.0, seed=7)
    assert r.seed == 7


# --- invalid nodes ---------------------------------------------------------

@pytest.mark.parametrize("model,bad_id", [
    (Problem, "PRB-1"), (Capability, "CAP-0001"), (Process, "PRC-01"), (Step, "PRC-001"), (Requirement, "REQ-X-001"),
])
def test_bad_id_format_rejected(model, bad_id):
    fields = {
        Problem: {"kind": "goal", "text": "x"},
        Capability: {"name": "x"},
        Process: {"name": "x"},
        Step: {"description": "x"},
        Requirement: {"kind": "functional", "statement": "x"},
    }[model]
    with pytest.raises(ValidationError):
        model(id=bad_id, **fields)


def test_requirement_kind_must_match_id():
    with pytest.raises(ValidationError, match="ID says functional"):
        Requirement(id="REQ-F-002", kind="non_functional", statement="x")


def test_empty_statement_rejected():
    with pytest.raises(ValidationError):
        Requirement(id="REQ-F-002", kind="functional", statement="   ")


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        Capability(id="CAP-002", name="x", parent="PRB-001")


def test_source_span_end_after_start():
    with pytest.raises(ValidationError):
        SourceSpan(start=10, end=10)


@pytest.mark.parametrize("confidence", [-0.1, 1.5])
def test_confidence_bounds(confidence):
    with pytest.raises(ValidationError):
        TraceLink(from_id="CAP-001", to_id="PRC-001", kind=LinkKind.CAPABILITY_PROCESS, confidence=confidence)


def test_self_link_rejected():
    with pytest.raises(ValidationError):
        TraceLink(from_id="CAP-001", to_id="CAP-001", kind=LinkKind.CAPABILITY_PROCESS)


# --- invalid graphs --------------------------------------------------------

def test_link_to_unknown_node_rejected():
    data = small_graph()
    data["links"].append({"from_id": "PRC-001", "to_id": "REQ-F-099", "kind": "process_requirement"})
    with pytest.raises(ValidationError, match="unknown node REQ-F-099"):
        TraceGraph.model_validate(data)


def test_link_with_wrong_endpoint_types_rejected():
    data = small_graph()
    data["links"].append({"from_id": "PRB-001", "to_id": "PRC-001", "kind": "problem_capability"})
    with pytest.raises(ValidationError, match="doesn't fit kind"):
        TraceGraph.model_validate(data)


def test_duplicate_link_rejected():
    data = small_graph()
    data["links"].append({"from_id": "PRB-001", "to_id": "CAP-001", "kind": "problem_capability"})
    with pytest.raises(ValidationError, match="duplicate link"):
        TraceGraph.model_validate(data)


def test_duplicate_node_id_rejected():
    data = small_graph()
    data["capabilities"].append({"id": "CAP-001", "name": "Another"})
    with pytest.raises(ValidationError, match="duplicate node IDs"):
        TraceGraph.model_validate(data)


def test_step_without_its_process_rejected():
    data = small_graph()
    data["steps"].append({"id": "PRC-009.1", "description": "Orphan step"})
    with pytest.raises(ValidationError, match="process is missing"):
        TraceGraph.model_validate(data)


# --- orphans are allowed but reported ---------------------------------------

def test_orphans_are_reported_not_rejected():
    data = small_graph()
    data["requirements"].append({"id": "REQ-F-002", "kind": "functional", "statement": "Unlinked requirement."})
    data["capabilities"].append({"id": "CAP-002", "name": "Unlinked capability"})
    g = TraceGraph.model_validate(data)
    assert g.orphans() == ["CAP-002", "REQ-F-002"]
