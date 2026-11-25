"""The mini test case (task 1.5) run through every piece built so far."""

from mamo.canonicalise import canonicalise
from mamo.store import Store


def by_statement(graph, start: str) -> str:
    """ID of the requirement or rule whose statement starts with `start`."""
    matches = [n.id for n in [*graph.requirements, *graph.rules] if n.statement.startswith(start)]
    assert len(matches) == 1, matches
    return matches[0]


def test_shape(mini_graph):
    g = mini_graph
    counts = (len(g.problems), len(g.capabilities), len(g.processes), len(g.steps), len(g.rules), len(g.requirements))
    assert counts == (4, 2, 6, 3, 2, 6)
    assert sorted(p.level for p in g.processes) == [2, 2, 3, 3, 4, 4]
    assert g.orphans() == []


def test_already_canonical(mini_graph):
    canonical, mapping = canonicalise(mini_graph)
    assert canonical == mini_graph
    assert all(old == new for old, new in mapping.items())


def test_source_spans_point_at_the_problem_text(mini_graph, mini_problem):
    for p in mini_graph.problems:
        assert mini_problem[p.source.start:p.source.end] == p.text
    for r in mini_graph.rules:
        assert r.source is not None
        assert 0 <= r.source.start < r.source.end <= len(mini_problem)


def test_round_trips_through_the_store(mini_graph):
    with Store() as s:
        s.save_graph("gold/mini_library", mini_graph)
        assert s.load_graph("gold/mini_library") == mini_graph


def test_rule_requirement_traces_back_to_its_problem(mini_graph):
    overlap_req = by_statement(mini_graph, "The system shall reject a booking that overlaps")
    up = mini_graph.upstream(overlap_req)
    double_booked = next(p.id for p in mini_graph.problems if p.text == "rooms are often double-booked")
    assert double_booked in up
    assert by_statement(mini_graph, "A room cannot have two bookings") in up


def test_shared_rule_links_two_branches(mini_graph):
    """The fee rule hangs off a booking step AND the membership L4: a change on the membership side
    reaches a booking requirement. This is the kind of path H6 (change impact) has to find."""
    fee_rule = by_statement(mini_graph, "Only members with a paid annual fee")
    parents = sorted(link.from_id for link in mini_graph.links if link.to_id == fee_rule)
    assert len(parents) == 2
    membership_cap = next(c.id for c in mini_graph.capabilities if c.name == "Membership management")
    fee_req = by_statement(mini_graph, "The system shall only accept bookings from members")
    assert fee_req in mini_graph.downstream(membership_cap)
