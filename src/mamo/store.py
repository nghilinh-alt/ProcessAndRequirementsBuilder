"""SQLite trace store (task 1.3).

One database file holds every run (and gold standard) side by side. Nodes and
links are stored as JSON next to their keys, so a graph loads back exactly as
it was saved. Agents can write one node or link at a time (the H3 trace-graph
design: agents read and write typed pieces, not whole transcripts); the full
structural checks from schemas.py run whenever a graph is loaded.

Gold standards are stored like runs, under an ID such as "gold/insurance".
The llm_calls table is created here and filled by the LLM wrapper (task 1.4).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Self

from mamo.schemas import (
    BusinessRule,
    Capability,
    Node,
    Problem,
    Process,
    Requirement,
    Run,
    Step,
    TraceGraph,
    TraceLink,
)

NODE_TYPES: dict[str, type] = {
    "problem": Problem,
    "capability": Capability,
    "process": Process,
    "step": Step,
    "rule": BusinessRule,
    "requirement": Requirement,
}
_TYPE_NAME = {cls: name for name, cls in NODE_TYPES.items()}
_GRAPH_FIELD = {
    "problem": "problems",
    "capability": "capabilities",
    "process": "processes",
    "step": "steps",
    "rule": "rules",
    "requirement": "requirements",
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS nodes (
    run_id TEXT NOT NULL,
    id TEXT NOT NULL,
    type TEXT NOT NULL,
    data TEXT NOT NULL,
    PRIMARY KEY (run_id, id)
);
CREATE TABLE IF NOT EXISTS links (
    run_id TEXT NOT NULL,
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    data TEXT NOT NULL,
    PRIMARY KEY (run_id, from_id, to_id),
    FOREIGN KEY (run_id, from_id) REFERENCES nodes (run_id, id),
    FOREIGN KEY (run_id, to_id) REFERENCES nodes (run_id, id)
);
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY,
    run_id TEXT,
    stage TEXT,
    model TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    temperature REAL,
    tokens_in INTEGER,
    tokens_out INTEGER,
    latency_ms INTEGER,
    cost_usd REAL,
    created_at TEXT NOT NULL
);
"""


class Store:
    """Open (or create) a trace database. Use as a context manager or call close()."""

    def __init__(self, path: str | Path = ":memory:"):
        self.db = sqlite3.connect(str(path))
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(_SCHEMA)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self.db.close()

    # --- runs ---------------------------------------------------------------
    def add_run(self, run: Run) -> None:
        with self.db:
            self.db.execute("INSERT INTO runs (id, data) VALUES (?, ?)", (run.id, run.model_dump_json()))

    def get_run(self, run_id: str) -> Run:
        row = self.db.execute("SELECT data FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return Run.model_validate_json(row[0])

    def run_ids(self) -> list[str]:
        """Every run or gold standard that has nodes, sorted."""
        return [r[0] for r in self.db.execute("SELECT DISTINCT run_id FROM nodes ORDER BY run_id")]

    # --- writing one piece at a time ------------------------------------------
    def add_node(self, run_id: str, node: Node) -> None:
        try:
            with self.db:
                self.db.execute(
                    "INSERT INTO nodes (run_id, id, type, data) VALUES (?, ?, ?, ?)",
                    (run_id, node.id, _TYPE_NAME[type(node)], node.model_dump_json()),
                )
        except sqlite3.IntegrityError as e:
            raise ValueError(f"{run_id}: node {node.id} already exists") from e

    def add_link(self, run_id: str, link: TraceLink) -> None:
        try:
            with self.db:
                self.db.execute(
                    "INSERT INTO links (run_id, from_id, to_id, kind, data) VALUES (?, ?, ?, ?, ?)",
                    (run_id, link.from_id, link.to_id, link.kind.value, link.model_dump_json()),
                )
        except sqlite3.IntegrityError as e:
            raise ValueError(
                f"{run_id}: link {link.from_id} -> {link.to_id} is a duplicate or points to a missing node"
            ) from e

    # --- whole graphs ---------------------------------------------------------
    def save_graph(self, run_id: str, graph: TraceGraph) -> None:
        """Write a whole (already validated) graph in one go. The run must not have nodes yet."""
        if self.db.execute("SELECT 1 FROM nodes WHERE run_id = ? LIMIT 1", (run_id,)).fetchone():
            raise ValueError(f"{run_id} already has nodes; use a new run ID")
        with self.db:
            for field in _GRAPH_FIELD.values():
                for node in getattr(graph, field):
                    self.db.execute(
                        "INSERT INTO nodes (run_id, id, type, data) VALUES (?, ?, ?, ?)",
                        (run_id, node.id, _TYPE_NAME[type(node)], node.model_dump_json()),
                    )
            for link in graph.links:
                self.db.execute(
                    "INSERT INTO links (run_id, from_id, to_id, kind, data) VALUES (?, ?, ?, ?, ?)",
                    (run_id, link.from_id, link.to_id, link.kind.value, link.model_dump_json()),
                )

    def load_graph(self, run_id: str) -> TraceGraph:
        """Read a run back as a TraceGraph. Runs all structural checks; raises if the stored graph breaks them."""
        groups: dict[str, list] = {field: [] for field in _GRAPH_FIELD.values()}
        rows = self.db.execute("SELECT type, data FROM nodes WHERE run_id = ? ORDER BY rowid", (run_id,))
        for type_name, data in rows:
            groups[_GRAPH_FIELD[type_name]].append(NODE_TYPES[type_name].model_validate_json(data))
        if not any(groups.values()):
            raise KeyError(run_id)
        links = [
            TraceLink.model_validate_json(data)
            for (data,) in self.db.execute("SELECT data FROM links WHERE run_id = ? ORDER BY rowid", (run_id,))
        ]
        stored_run_id = None if run_id.startswith("gold/") else run_id
        return TraceGraph(run_id=stored_run_id, links=links, **groups)

    # --- reading pieces -------------------------------------------------------
    def get_nodes(self, run_id: str, type_name: str) -> list[Node]:
        """All nodes of one type ("process", "rule", ...) in a run, in the order they were written."""
        cls = NODE_TYPES[type_name]
        rows = self.db.execute(
            "SELECT data FROM nodes WHERE run_id = ? AND type = ? ORDER BY rowid", (run_id, type_name)
        )
        return [cls.model_validate_json(data) for (data,) in rows]

    def get_chain(self, run_id: str, node_id: str) -> list[str]:
        """Everything a node traces back to, e.g. requirement -> rule/step -> L4 ... -> capability -> problem."""
        return self.load_graph(run_id).upstream(node_id)
