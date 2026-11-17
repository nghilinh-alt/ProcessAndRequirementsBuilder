from datetime import datetime

import pytest
from pydantic import ValidationError

from mamo.schemas import (
    BusinessRule,
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
    """A tiny valid graph as plain data.

    PRB-001 -> CAP-001 (L1) -> PRC-001 (L2) -> PRC-002 (L3) -> PRC-003 (L4) -> step PRC-003.1
    Rule RUL-001 applies to PRC-003 and step PRC-003.1. Requirements hang off the step, the rule and the L3.
    """
    data = {
        "problems": [{"id": "PRB-001", "kind": "pain_point", "text": "Claim payments are reconciled by hand.",
                      "source": {"start": 0, "end": 38}}],
        "capabilities": [{"id": "CAP-001", "name": "Claims finance"}],
        "processes": [
            {"id": "PRC-001", "level": 2, "name": "Manage claim payments"},
            {"id": "PRC-002", "level": 3, "name": "Process a claim payment"},
            {"id": "PRC-003", "level": 4, "name": "Approve the payment", "actors": ["Finance officer"]},
        ],
        "steps": [{"id": "PRC-003.1", "description": "Check the approver's delegation limit", "actor": "Finance officer"}],
        "rules": [{"id": "RUL-001", "statement": "Payments over $10,000 need a second approver."}],
        "requirements": [
            {"id": "REQ-F-001", "kind": "functional",
             "statement": "The system shall check the approver's delegation limit before approval."},
            {"id": "REQ-F-002", "kind": "functional",
             "statement": "The system shall require a second approver for payments over $10,000."},
            {"id": "REQ-N-001", "kind": "non_functional",
             "statement": "Payment records shall be retained for 7 years.", "must_have": False},
        ],
        "links": [
            {"from_id": "PRB-001", "to_id": "CAP-001", "kind": "problem_capability"},
            {"from_id": "CAP-001", "to_id": "PRC-001", "kind": "capability_process"},
            {"from_id": "PRC-001", "to_id": "PRC-002", "kind": "process_process"},
            {"from_id": "PRC-002", "to_id": "PRC-003", "kind": "process_process"},
            {"from_id": "PRC-003", "to_id": "RUL-001", "kind": "process_rule"},
            {"from_id": "PRC-003.1", "to_id": "RUL-001", "kind": "process_rule"},
            {"from_id": "PRC-003.1", "to_id": "REQ-F-001", "kind": "process_requirement", "confidence": 0.9},
            {"from_id": "RUL-001", "to_id": "REQ-F-002", "kind": "rule_requirement"},
            {"from_id": "PRC-002", "to_id": "REQ-N-001", "kind": "process_requirement"},
        ],
    }
    data.update(overrides)
    return data


def add_link(data: dict, from_id: str, to_id: str, kind: str) -> dict:
    data["links"].append({"from_id": from_id, "to_id": to_id, "kind": kind})
    return data


# --- valid objects ---------------------------------------------------------

def test_valid_graph_loads_and_has_no_orphans():
    g = TraceGraph.model_validate(small_graph())
    assert len(g.nodes()) == 10
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
    (BusinessRule, "RUL-01"),
])
def test_bad_id_format_rejected(model, bad_id):
    fields = {
        Problem: {"kind": "goal", "text": "x"},
        Capability: {"name": "x"},
        Process: {"name": "x", "level": 2},
        Step: {"description": "x"},
        Requirement: {"kind": "functional", "statement": "x"},
        BusinessRule: {"statement": "x"},
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
    add_link(data, "PRC-001", "REQ-F-099", "process_requirement")
    with pytest.raises(ValidationError, match="unknown node REQ-F-099"):
        TraceGraph.model_validate(data)


def test_link_with_wrong_endpoint_types_rejected():
    data = small_graph()
    add_link(data, "PRB-001", "PRC-001", "problem_capability")
    with pytest.raises(ValidationError, match="doesn't fit kind"):
        TraceGraph.model_validate(data)


def test_duplicate_link_rejected():
    data = small_graph()
    add_link(data, "PRB-001", "CAP-001", "problem_capability")
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
    data["requirements"].append({"id": "REQ-F-009", "kind": "functional", "statement": "Unlinked requirement."})
    data["capabilities"].append({"id": "CAP-002", "name": "Unlinked capability"})
    data["rules"].append({"id": "RUL-002", "statement": "Unlinked rule."})
    data["processes"].append({"id": "PRC-009", "level": 3, "name": "Unlinked L3"})
    g = TraceGraph.model_validate(data)
    assert g.orphans() == ["CAP-002", "PRC-009", "REQ-F-009", "RUL-002"]


# --- hierarchy (task 1.1b) -------------------------------------------------

def test_process_level_must_be_2_to_4():
    with pytest.raises(ValidationError):
        Process(id="PRC-001", level=5, name="Too deep")


def test_capability_must_link_to_l2():
    data = small_graph()
    add_link(data, "CAP-001", "PRC-002", "capability_process")  # PRC-002 is L3
    with pytest.raises(ValidationError, match="must link to an L2"):
        TraceGraph.model_validate(data)


def test_process_link_must_go_down_one_level():
    data = small_graph()
    data["processes"].append({"id": "PRC-004", "level": 4, "name": "Skips a level"})
    add_link(data, "PRC-001", "PRC-004", "process_process")  # L2 -> L4
    with pytest.raises(ValidationError, match="exactly one level"):
        TraceGraph.model_validate(data)


def test_process_link_cannot_go_up():
    data = small_graph()
    data["processes"].append({"id": "PRC-004", "level": 2, "name": "Another L2"})
    add_link(data, "PRC-003", "PRC-004", "process_process")  # L4 -> L2
    with pytest.raises(ValidationError, match="exactly one level"):
        TraceGraph.model_validate(data)


def test_process_has_only_one_parent():
    data = small_graph()
    data["processes"].append({"id": "PRC-004", "level": 2, "name": "Another L2"})
    add_link(data, "CAP-001", "PRC-004", "capability_process")
    add_link(data, "PRC-004", "PRC-002", "process_process")  # PRC-002 already under PRC-001
    with pytest.raises(ValidationError, match="more than one parent"):
        TraceGraph.model_validate(data)


def test_steps_only_under_l4():
    data = small_graph()
    data["steps"].append({"id": "PRC-002.1", "description": "Step under an L3"})
    with pytest.raises(ValidationError, match="L4 activity"):
        TraceGraph.model_validate(data)


def test_rule_can_apply_to_several_processes():
    data = small_graph()
    add_link(data, "PRC-002", "RUL-001", "process_rule")  # third process/step for the same rule
    g = TraceGraph.model_validate(data)
    parents = sorted(link.from_id for link in g.links if link.to_id == "RUL-001")
    assert parents == ["PRC-002", "PRC-003", "PRC-003.1"]


def test_rule_cannot_link_to_process():
    data = small_graph()
    add_link(data, "RUL-001", "PRC-003", "process_rule")
    with pytest.raises(ValidationError, match="doesn't fit kind"):
        TraceGraph.model_validate(data)


# --- tracing forwards and backwards -----------------------------------------

def test_backward_trace_from_requirement_reaches_problem():
    g = TraceGraph.model_validate(small_graph())
    assert g.upstream("REQ-F-002") == [
        "CAP-001", "PRB-001", "PRC-001", "PRC-002", "PRC-003", "PRC-003.1", "RUL-001",
    ]


def test_forward_trace_from_rule_finds_its_requirements():
    g = TraceGraph.model_validate(small_graph())
    assert g.downstream("RUL-001") == ["REQ-F-002"]


def test_forward_trace_from_l3_includes_activity_steps_rules_and_requirements():
    g = TraceGraph.model_validate(small_graph())
    assert g.downstream("PRC-002") == [
        "PRC-003", "PRC-003.1", "REQ-F-001", "REQ-F-002", "REQ-N-001", "RUL-001",
    ]


def test_trace_unknown_node_raises():
    g = TraceGraph.model_validate(small_graph())
    with pytest.raises(KeyError):
        g.downstream("PRC-999")
