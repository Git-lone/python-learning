"""SQLite-backed approval workflow; deliberately no real external write."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path
import sqlite3
from typing import Any, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict, total=False):
    request_id: str
    draft: str
    approved: bool
    result: str


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = path
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS deliveries "
                "(request_id TEXT PRIMARY KEY, body TEXT NOT NULL)"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def publish(self, request_id: str, body: str) -> str:
        if not request_id or not body:
            raise ValueError("request_id and body are required")
        # The unique key and payload check live in the same business transaction.
        with self._connect() as db:
            db.execute("INSERT OR IGNORE INTO deliveries VALUES (?, ?)", (request_id, body))
            saved = db.execute(
                "SELECT body FROM deliveries WHERE request_id=?", (request_id,)
            ).fetchone()
            if saved is None or saved[0] != body:
                raise ValueError("idempotency key reused with different payload")
        return f"published:{request_id}"

    def count(self) -> int:
        with self._connect() as db:
            return int(db.execute("SELECT count(*) FROM deliveries").fetchone()[0])


def build_graph(checkpointer: SqliteSaver, ledger: Ledger) -> Any:
    def approve(state: State) -> State:
        answer = interrupt({"request_id": state["request_id"], "draft": state["draft"]})
        if not isinstance(answer, bool):
            raise ValueError("approval must be a boolean")
        return {"approved": answer}

    def publish(state: State) -> State:
        result = (
            ledger.publish(state["request_id"], state["draft"]) if state["approved"] else "rejected"
        )
        return {"result": result}

    graph = StateGraph(State)
    graph.add_node("approve", approve)
    graph.add_node("publish", publish)
    graph.add_edge(START, "approve")
    graph.add_edge("approve", "publish")
    graph.add_edge("publish", END)
    return graph.compile(checkpointer=checkpointer)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "approve", "reject"])
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--thread", default="demo-thread")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(args.directory / "ledger.sqlite")
    config = {"configurable": {"thread_id": args.thread}}
    with SqliteSaver.from_conn_string(str(args.directory / "checkpoints.sqlite")) as saver:
        graph = build_graph(saver, ledger)
        state = graph.get_state(config)
        if args.action == "start":
            if state.values:
                parser.error("thread already exists; resume it or choose a new --thread")
            result = graph.invoke({"request_id": args.thread, "draft": "Synthetic reply"}, config)
        else:
            if not state.next:
                parser.error("thread has no pending approval")
            result = graph.invoke(Command(resume=args.action == "approve"), config)
        print("waiting_approval" if result.get("__interrupt__") else result["result"])
        print(f"deliveries={ledger.count()}")


if __name__ == "__main__":
    main()
