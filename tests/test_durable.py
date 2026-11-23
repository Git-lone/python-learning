from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
import pytest

from agent_lab.durable import Ledger, build_graph, inspect_workflow


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


@pytest.mark.parametrize("approval", [True, False])
def test_inspect_observes_pause_and_result_without_resuming(tmp_path, approval):
    database = str(tmp_path / "checkpoints.sqlite")
    ledger = Ledger(tmp_path / "ledger.sqlite")
    config = {"configurable": {"thread_id": "workflow-1"}}
    with SqliteSaver.from_conn_string(database) as saver:
        graph = build_graph(saver, ledger)
        graph.invoke({"request_id": "business-1", "draft": "reply"}, config)

    assert inspect_workflow(tmp_path, "workflow-1") == {
        "checkpoint_found": True,
        "request_id": "business-1",
        "approved": None,
        "result": None,
        "deliveries_total": 0,
        "deliveries_for_request": 0,
    }
    # 观察后仍停在原审批节点；业务请求 ID 故意与流程 ID 不同，避免误按 thread 查账本。
    with SqliteSaver.from_conn_string(database) as saver:
        graph = build_graph(saver, ledger)
        assert graph.get_state(config).next == ("approve",)
        assert ledger.count() == 0
        graph.invoke(Command(resume=approval), config)

    expected_count = int(approval)
    assert inspect_workflow(tmp_path, "workflow-1") == {
        "checkpoint_found": True,
        "request_id": "business-1",
        "approved": approval,
        "result": "published:business-1" if approval else "rejected",
        "deliveries_total": expected_count,
        "deliveries_for_request": expected_count,
    }
    assert inspect_workflow(tmp_path, "unknown") == {
        "checkpoint_found": False,
        "request_id": None,
        "approved": None,
        "result": None,
        "deliveries_total": expected_count,
        "deliveries_for_request": None,
    }
    assert ledger.count() == expected_count


def test_inspect_cli_does_not_create_missing_directory(tmp_path):
    directory = tmp_path / "not-created"
    result = subprocess.run(
        [sys.executable, "-m", "agent_lab.durable", "inspect", "--directory", str(directory)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 2
    assert "database file not found" in result.stderr
    assert not directory.exists()


def test_inspect_does_not_initialize_missing_ledger(tmp_path):
    # 只有检查点库时也应先报缺文件，不能像执行流程那样自动初始化业务账本。
    with SqliteSaver.from_conn_string(str(tmp_path / "checkpoints.sqlite")) as saver:
        saver.setup()
    with pytest.raises(FileNotFoundError, match="ledger.sqlite"):
        inspect_workflow(tmp_path, "unknown")
    assert not (tmp_path / "ledger.sqlite").exists()
