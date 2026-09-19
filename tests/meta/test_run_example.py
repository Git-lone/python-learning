from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from tools.content_model import ExampleRun, ExecutionResult, ExpectedException
from tools.run_example import (
    EXAMPLE_EXCEPTION_MESSAGE,
    EXAMPLE_EXIT_CODE,
    EXAMPLE_INPUT_MISSING,
    EXAMPLE_OUTPUT_DECODE,
    EXAMPLE_PATH_OUTSIDE_REPO,
    EXAMPLE_START_FAILED,
    EXAMPLE_STDOUT_MISSING,
    EXAMPLE_TIMEOUT,
    ExampleContractError,
    main,
    run_example,
    validate_execution_contract,
    verify_execution,
)


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _record(
    repo: Path,
    script: Path,
    *,
    command: tuple[str, ...] | None = None,
    timeout: int = 5,
    exit_code: int = 0,
    stdout: tuple[str, ...] = (),
    stderr: tuple[str, ...] = (),
    expected_exception: ExpectedException | None = None,
    input_files: tuple[Path, ...] = (),
) -> ExampleRun:
    return ExampleRun(
        example_id="demo",
        source=script.relative_to(repo),
        python_spec=">=3.12,<3.14",
        dependencies=(),
        working_directory=Path("."),
        input_preparation="无需准备",
        command=command or ("python", script.relative_to(repo).as_posix()),
        timeout_seconds=timeout,
        expected_exit_code=exit_code,
        stdout_contains=stdout,
        stderr_contains=stderr,
        expected_exception=expected_exception,
        requirements=("3.8",),
        input_files=input_files,
    )


def test_run_uses_current_interpreter_argument_list_and_unordered_utf8_fragments(
    tmp_path: Path,
) -> None:
    script = _write(
        tmp_path / "example.py",
        """
        import sys

        print("后到片段：世界")
        print(f"解释器：{sys.executable}")
        print(f"参数：{sys.argv[1]}")
        print("先到片段：你好")
        print("ValueError: 教学异常")
        """,
    )
    record = _record(
        tmp_path,
        script,
        command=("python", "example.py", "含 空格参数"),
        stdout=("先到片段：你好", "后到片段：世界", "参数：含 空格参数"),
        expected_exception=ExpectedException("ValueError", "教学异常"),
    )

    result = run_example(record, tmp_path)

    assert result.exit_code == 0
    assert f"解释器：{sys.executable}" in result.stdout
    assert verify_execution(record, result) == ()


def test_contract_rejects_outside_paths_and_missing_input(tmp_path: Path) -> None:
    script = _write(tmp_path / "example.py", "print('ok')")
    record = _record(
        tmp_path,
        script,
        input_files=(Path("missing.json"), Path("../outside.json")),
    )

    issues = validate_execution_contract(record, tmp_path)

    assert {issue.code for issue in issues} == {
        EXAMPLE_INPUT_MISSING,
        EXAMPLE_PATH_OUTSIDE_REPO,
    }
    with pytest.raises(ExampleContractError):
        run_example(record, tmp_path)


def test_timeout_terminates_process_and_reports_stable_diagnostic(
    tmp_path: Path,
) -> None:
    script = _write(
        tmp_path / "slow.py",
        """
        import time

        print("已启动", flush=True)
        time.sleep(10)
        """,
    )
    record = _record(tmp_path, script, timeout=1, stdout=("已启动",))

    result = run_example(record, tmp_path)
    issues = verify_execution(record, result)

    assert result.timed_out is True
    assert result.exit_code is None
    assert "已启动" in result.stdout
    assert [issue.code for issue in issues] == [EXAMPLE_TIMEOUT]
    assert result.duration_seconds < 4


def test_invalid_utf8_output_is_preserved_and_reported(tmp_path: Path) -> None:
    script = _write(
        tmp_path / "invalid_utf8.py",
        """
        import sys

        sys.stdout.buffer.write(b"valid\\xfftail")
        """,
    )
    record = _record(tmp_path, script)

    result = run_example(record, tmp_path)
    issues = verify_execution(record, result)

    assert "valid�tail" in result.stdout
    assert [issue.code for issue in issues] == [EXAMPLE_OUTPUT_DECODE]


def test_start_failure_is_converted_to_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _write(tmp_path / "example.py", "print('ok')")
    record = _record(tmp_path, script)

    def fail_to_start(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
        raise OSError("受控启动失败")

    monkeypatch.setattr(subprocess, "Popen", fail_to_start)
    result = run_example(record, tmp_path)
    issues = verify_execution(record, result)

    assert result.exit_code is None
    assert [issue.code for issue in issues] == [EXAMPLE_START_FAILED]
    assert "受控启动失败" in issues[0].message


def test_verifier_reports_exit_output_and_expected_exception_independently() -> None:
    record = ExampleRun(
        example_id="failure-demo",
        source=Path("example.py"),
        python_spec=">=3.12,<3.14",
        dependencies=(),
        working_directory=Path("."),
        input_preparation="无需准备",
        command=("python", "example.py"),
        timeout_seconds=5,
        expected_exit_code=0,
        stdout_contains=("第一片段", "第二片段"),
        stderr_contains=(),
        expected_exception=ExpectedException("ValueError", "指定消息"),
        requirements=("3.9",),
    )
    result = ExecutionResult(2, "第二片段\nValueError", "", 0.1, False)

    issues = verify_execution(record, result)

    assert {issue.code for issue in issues} == {
        EXAMPLE_EXIT_CODE,
        EXAMPLE_STDOUT_MISSING,
        EXAMPLE_EXCEPTION_MESSAGE,
    }
    missing = next(issue for issue in issues if issue.code == EXAMPLE_STDOUT_MISSING)
    assert "任意顺序" in missing.message


def _make_course(repo: Path) -> None:
    _write(repo / "chapters/01-basics/README.md", "# 基础语法")
    _write(repo / "chapters/01-basics/examples/main.py", "print('章节完成')")
    _write(repo / "chapters/01-basics/exercises/exercise_01.py", "pass")
    _write(
        repo / "catalog.toml",
        """
        audience = ["具备 Java 基础"]
        python_spec = ">=3.12,<3.14"

        [[chapters]]
        number = 1
        chapter_id = "CH01"
        title = "基础语法"
        directory = "chapters/01-basics"
        entry = "chapters/01-basics/README.md"
        prerequisites = []
        """,
    )
    _write(
        repo / "chapters/01-basics/chapter.toml",
        """
        chapter_id = "CH01"
        requirements = ["3.3", "3.8"]

        [[topics]]
        topic_id = "variables"
        title = "变量"
        comparison_anchor = "compare-variables"
        requirements = ["3.8"]

        [[comparison_cards]]
        topic_id = "variables"
        shared_purpose = "保存值"
        observable_difference = "可重新绑定"
        python_use_case = "脚本"
        java_pitfall = "类型固定"
        correction = "区分名称和对象"

        [[examples]]
        example_id = "basics-main"
        source = "chapters/01-basics/examples/main.py"
        python_spec = ">=3.12,<3.14"
        dependencies = []
        working_directory = "."
        input_preparation = "无需准备"
        command = ["python", "chapters/01-basics/examples/main.py"]
        timeout_seconds = 5
        expected_exit_code = 0
        stdout_contains = ["章节完成"]
        stderr_contains = []
        requirements = ["3.8"]

        [[boundaries]]
        boundary_id = "variables-empty"
        topic_id = "variables"
        input = "空"
        expected_behavior = "保持为空"
        requirements = ["3.8"]

        [[exercises]]
        exercise_id = "CH01-EX01"
        title = "练习"
        entry = "chapters/01-basics/exercises/exercise_01.py"
        acceptance_id = "ACC-01"
        observable_goal = "完成"

        [[acceptances]]
        acceptance_id = "ACC-01"
        exercise_id = "CH01-EX01"
        kind = "behavior"

        [acceptances.behavior]
        input = "空"
        operation = "执行"
        observable_result = "完成"
        """,
    )


def test_cli_supports_chapter_and_all_selection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_course(tmp_path)

    chapter_exit = main(["--chapter", "01"], repo_root=tmp_path)
    chapter_output = capsys.readouterr()
    all_exit = main(["--all"], repo_root=tmp_path)
    all_output = capsys.readouterr()

    assert chapter_exit == 0
    assert "PASS | CH01 | basics-main" in chapter_output.out
    assert "已通过 1 个示例" in chapter_output.out
    assert all_exit == 0
    assert "PASS | CH01 | basics-main" in all_output.out
    assert "已通过 1 个示例" in all_output.out
