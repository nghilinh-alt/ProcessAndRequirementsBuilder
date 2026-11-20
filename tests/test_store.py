from datetime import datetime

import pytest
from test_schemas import small_graph

from mamo.schemas import Capability, LinkKind, Process, Run, TraceGraph, TraceLink
from mamo.store import Store


@pytest.fixture
def store():
    with Store() as s:
        yield s


@pytest.fixture
def graph() -> TraceGraph:
    return TraceGraph.model_validate(small_graph())


def test_graph_round_trips_exactly(store, graph):
    store.save_graph("run-001", graph)
    assert store.load_graph("run-001") == graph.model_copy(update={"run_id": "run-001"})


def test_gold_standard_loads_with_no_run_id(store, graph):
    store.save_graph("gold/insurance", graph)
    assert store.load_graph("gold/insurance").run_id is None


def test_saved_to_file_survives_reopening(tmp_path, graph):
    path = tmp_path / "mamo.db"
    with Store(path) as s:
        s.save_graph("run-001", graph)
    with Store(path) as s:
        assert s.load_graph("run-001").nodes().keys() == graph.nodes().keys()


def test_runs_are_kept_apart(store, graph):
    store.save_graph("run-001", graph)
    store.save_graph("run-002", graph)
    store.add_node("run-002", Capability(id="CAP-002", name="Only in run 2"))
    assert "CAP-002" not in store.load_graph("run-001").nodes()
    assert store.run_ids() == ["run-001", "run-002"]


def test_cannot_save_over_an_existing_run(store, graph):
    store.save_graph("run-001", graph)
    with pytest.raises(ValueError, match="already has nodes"):
        store.save_graph("run-001", graph)


def test_agents_can_write_piece_by_piece(store):
    store.add_node("run-001", Capability(id="CAP-001", name="Claims finance"))
    store.add_node("run-001", Process(id="PRC-001", level=2, name="Manage claim payments"))
    store.add_link("run-001", TraceLink(from_id="CAP-001", to_id="PRC-001", kind=LinkKind.CAPABILITY_PROCESS))
    g = store.load_graph("run-001")
    assert g.orphans() == ["CAP-001"]  # no problem link yet: allowed, and reported


def test_duplicate_node_rejected(store):
    store.add_node("run-001", Capability(id="CAP-001", name="A"))
    with pytest.raises(ValueError, match="already exists"):
        store.add_node("run-001", Capability(id="CAP-001", name="B"))


def test_link_to_missing_node_rejected(store):
    store.add_node("run-001", Capability(id="CAP-001", name="A"))
    with pytest.raises(ValueError, match="missing node"):
        store.add_link("run-001", TraceLink(from_id="CAP-001", to_id="PRC-001", kind=LinkKind.CAPABILITY_PROCESS))


def test_load_runs_the_structure_checks(store):
    # Each piece is valid on its own, but a capability may only link to an L2
    store.add_node("run-001", Capability(id="CAP-001", name="A"))
    store.add_node("run-001", Process(id="PRC-001", level=3, name="An L3"))
    store.add_link("run-001", TraceLink(from_id="CAP-001", to_id="PRC-001", kind=LinkKind.CAPABILITY_PROCESS))
    with pytest.raises(ValueError, match="must link to an L2"):
        store.load_graph("run-001")


def test_get_nodes_by_type(store, graph):
    store.save_graph("run-001", graph)
    assert [p.level for p in store.get_nodes("run-001", "process")] == [2, 3, 4]
    assert [r.id for r in store.get_nodes("run-001", "rule")] == ["RUL-001"]


def test_get_chain_traces_requirement_to_problem(store, graph):
    store.save_graph("run-001", graph)
    assert store.get_chain("run-001", "REQ-F-002") == [
        "CAP-001", "PRB-001", "PRC-001", "PRC-002", "PRC-003", "PRC-003.1", "RUL-001",
    ]


def test_unknown_run_raises(store):
    with pytest.raises(KeyError):
        store.load_graph("run-999")


def test_run_record_round_trips(store):
    run = Run(id="run-001", case="insurance", started_at=datetime(2026, 12, 22, 10, 0), model="claude-x",
              temperature=0.0, seed=7)
    store.add_run(run)
    assert store.get_run("run-001") == run


def test_llm_calls_table_ready_for_task_1_4(store):
    cols = [row[1] for row in store.db.execute("PRAGMA table_info(llm_calls)")]
    assert {"model", "prompt_hash", "tokens_in", "tokens_out", "latency_ms", "cost_usd"} <= set(cols)
