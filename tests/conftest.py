from pathlib import Path

import pytest
import yaml

from mamo.schemas import TraceGraph

MINI = Path(__file__).parent / "fixtures" / "mini_library"


@pytest.fixture
def mini_problem() -> str:
    """Problem text of the mini test case (task 1.5)."""
    return (MINI / "problem.md").read_text(encoding="utf-8").rstrip("\n")


@pytest.fixture
def mini_graph() -> TraceGraph:
    """The mini test case: community library room bookings (task 1.5)."""
    return TraceGraph.model_validate(yaml.safe_load((MINI / "graph.yaml").read_text(encoding="utf-8")))
