import re

from test_schemas import add_link, small_graph

from mamo.canonicalise import canonicalise
from mamo.schemas import TraceGraph

SCRAMBLE = {
    "PRB-001": "PRB-042",
    "CAP-001": "CAP-007",
    "PRC-001": "PRC-090", "PRC-002": "PRC-015", "PRC-003": "PRC-033",
    "RUL-001": "RUL-005",
    "REQ-F-001": "REQ-F-020", "REQ-F-002": "REQ-F-003", "REQ-N-001": "REQ-N-009",
}


def scrambled(data: dict) -> dict:
    """Same content, different IDs and reversed list order: what a second LLM run might hand back."""
    def new(old: str) -> str:
        if re.fullmatch(r"PRC-\d{3}\.\d+", old):
            parent, n = old.split(".")
            return f"{SCRAMBLE[parent]}.{n}"
        return SCRAMBLE[old]

    out = {}
    for group, items in data.items():
        rows = []
        for item in items:
            item = dict(item)
            if group == "links":
                item["from_id"], item["to_id"] = new(item["from_id"]), new(item["to_id"])
            else:
                item["id"] = new(item["id"])
            rows.append(item)
        out[group] = list(reversed(rows))
    return out


def canon(data: dict) -> TraceGraph:
    return canonicalise(TraceGraph.model_validate(data))[0]


def test_scrambled_ids_and_order_give_identical_output():
    assert canon(scrambled(small_graph())) == canon(small_graph())


def test_canonical_ids_follow_the_tree():
    g = canon(scrambled(small_graph()))
    names = {p.name: (p.id, p.level) for p in g.processes}
    assert names == {
        "Manage claim payments": ("PRC-001", 2),
        "Process a claim payment": ("PRC-002", 3),
        "Approve the payment": ("PRC-003", 4),
    }
    assert [s.id for s in g.steps] == ["PRC-003.1"]
    assert [r.id for r in g.rules] == ["RUL-001"]


def test_requirements_numbered_by_tree_position_then_statement():
    g = canon(small_graph())
    by_statement = {r.statement: r.id for r in g.requirements}
    # RUL-001's earliest parent is the L4 activity PRC-003 itself, which comes before its step PRC-003.1,
    # so the rule's requirement is numbered before the step's requirement.
    assert by_statement["The system shall require a second approver for payments over $10,000."] == "REQ-F-001"
    assert by_statement["The system shall check the approver's delegation limit before approval."] == "REQ-F-002"
    assert by_statement["Payment records shall be retained for 7 years."] == "REQ-N-001"


def test_canonicalise_is_idempotent():
    once = canon(small_graph())
    twice = canonicalise(once)[0]
    assert twice == once


def test_mapping_covers_every_node():
    g = TraceGraph.model_validate(scrambled(small_graph()))
    _, mapping = canonicalise(g)
    assert set(mapping) == set(g.nodes())
    assert mapping["PRC-090"] == "PRC-001"


def test_whitespace_collapsed_case_kept():
    data = small_graph()
    data["rules"][0]["statement"] = "Payments  over $10,000\n  need a SECOND approver."
    g = canon(data)
    assert g.rules[0].statement == "Payments over $10,000 need a SECOND approver."


def test_step_order_kept_and_renumbered():
    data = small_graph()
    data["steps"] = [
        {"id": "PRC-003.7", "description": "Notify finance"},
        {"id": "PRC-003.2", "description": "Check delegation limit"},
        {"id": "PRC-003.5", "description": "Record approval"},
    ]
    data["links"] = [lk for lk in data["links"] if not lk["from_id"].startswith("PRC-003.")]
    g = canon(data)
    assert [(s.id, s.description) for s in g.steps] == [
        ("PRC-003.1", "Check delegation limit"),
        ("PRC-003.2", "Record approval"),
        ("PRC-003.3", "Notify finance"),
    ]


def test_siblings_sorted_by_name_whatever_the_input_ids():
    data = small_graph()
    data["processes"].append({"id": "PRC-004", "level": 3, "name": "Adjust a claim payment"})
    add_link(data, "PRC-001", "PRC-004", "process_process")
    g = canon(data)
    l3 = sorted((p.id, p.name) for p in g.processes if p.level == 3)
    # "Adjust..." sorts before "Process..." so it takes PRC-002, and "Process..." and its L4 move down
    assert l3 == [("PRC-002", "Adjust a claim payment"), ("PRC-003", "Process a claim payment")]
    assert {p.name: p.id for p in g.processes}["Approve the payment"] == "PRC-004"


def test_unlinked_nodes_go_last():
    data = small_graph()
    data["processes"].append({"id": "PRC-009", "level": 2, "name": "A floating L2"})
    data["requirements"].append({"id": "REQ-F-009", "kind": "functional", "statement": "A floating requirement."})
    g = canon(data)
    assert {p.name: p.id for p in g.processes}["A floating L2"] == "PRC-004"
    assert {r.statement: r.id for r in g.requirements}["A floating requirement."] == "REQ-F-003"
