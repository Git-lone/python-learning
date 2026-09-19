"""综合项目的行为测试。"""

from pathlib import Path

import pytest

from capstone.starter.task_reporter import (
    Task,
    TaskDataError,
    completion_rate,
    load_tasks,
    render_report,
)
from capstone.starter.task_reporter.cli import main


def test_report_orders_pending_tasks_and_calculates_rate() -> None:
    tasks = [
        Task("Deploy", "Bob", 30),
        Task("Code", "Alice", 60, done=True),
        Task("Document", "Alice", 15),
    ]

    report = render_report(tasks)

    assert completion_rate(tasks) == pytest.approx(1 / 3)
    assert report.index("[Alice] Document") < report.index("[Bob] Deploy")
    assert "completed: 1/3 (33.3%)" in report


def test_invalid_json_is_exposed_as_domain_error(tmp_path: Path) -> None:
    source = tmp_path / "tasks.json"
    source.write_text("not-json", encoding="utf-8")

    with pytest.raises(TaskDataError, match="cannot read task data") as captured:
        load_tasks(source)

    assert captured.value.__cause__ is not None


def test_cli_can_filter_owner(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "tasks.json"
    source.write_text(
        '[{"title":"Code","owner":"Alice","estimate_minutes":30,"done":false},'
        '{"title":"Test","owner":"Bob","estimate_minutes":20,"done":false}]',
        encoding="utf-8",
    )

    exit_code = main(["--input", str(source), "--owner", "Bob"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "[Bob] Test" in output
    assert "Alice" not in output
