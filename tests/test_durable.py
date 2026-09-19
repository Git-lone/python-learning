from concurrent.futures import ThreadPoolExecutor

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
import pytest

from agent_lab.durable import Ledger, build_graph


@pytest.mark.parametrize("approval, expected", [(True, 1), (False, 0)])
def test_restart_then_approve_or_reject(tmp_path, approval, expected):
    db = str(tmp_path / "checkpoint.sqlite")
    ledger = Ledger(tmp_path / "ledger.sqlite")
    config = {"configurable": {"thread_id": "a"}}
    with SqliteSaver.from_conn_string(db) as saver:
        graph = build_graph(saver, ledger)
        paused = graph.invoke({"request_id": "r1", "draft": "reply"}, config)
        assert paused["__interrupt__"]
        assert ledger.count() == 0
    with SqliteSaver.from_conn_string(db) as saver:
        graph = build_graph(saver, ledger)
        assert not graph.get_state({"configurable": {"thread_id": "other"}}).values
        result = graph.invoke(Command(resume=approval), config)
        assert result["result"] == ("published:r1" if approval else "rejected")
        assert ledger.count() == expected


def test_replayed_business_operation_is_idempotent_and_payload_bound(tmp_path):
    ledger = Ledger(tmp_path / "ledger.sqlite")
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert (
            list(pool.map(lambda _: ledger.publish("r1", "body"), range(8))) == ["published:r1"] * 8
        )
    assert ledger.count() == 1
    with pytest.raises(ValueError, match="different payload"):
        ledger.publish("r1", "changed")
    assert ledger.count() == 1


def test_non_boolean_approval_never_publishes(tmp_path):
    ledger = Ledger(tmp_path / "ledger.sqlite")
    with SqliteSaver.from_conn_string(str(tmp_path / "checkpoint.sqlite")) as saver:
        graph = build_graph(saver, ledger)
        config = {"configurable": {"thread_id": "a"}}
        graph.invoke({"request_id": "r1", "draft": "reply"}, config)
        with pytest.raises(ValueError, match="boolean"):
            graph.invoke(Command(resume="false"), config)
    assert ledger.count() == 0
