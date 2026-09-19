"""按章节清单执行示例并校验其可观察执行契约。"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Sequence

from tools.content_model import (
    ContentModelError,
    ExampleRun,
    ExecutionResult,
    Issue,
    load_catalog,
    load_chapter_manifest,
    sort_issues,
)

EXAMPLE_PATH_OUTSIDE_REPO = "EXAMPLE-PATH-OUTSIDE-REPO"
EXAMPLE_SOURCE_MISSING = "EXAMPLE-SOURCE-MISSING"
EXAMPLE_WORKDIR_MISSING = "EXAMPLE-WORKDIR-MISSING"
EXAMPLE_INPUT_MISSING = "EXAMPLE-INPUT-MISSING"
EXAMPLE_COMMAND_INVALID = "EXAMPLE-COMMAND-INVALID"
EXAMPLE_TIMEOUT_INVALID = "EXAMPLE-TIMEOUT-INVALID"
EXAMPLE_START_FAILED = "EXAMPLE-START-FAILED"
EXAMPLE_TIMEOUT = "EXAMPLE-TIMEOUT"
EXAMPLE_EXIT_CODE = "EXAMPLE-EXIT-CODE"
EXAMPLE_OUTPUT_DECODE = "EXAMPLE-OUTPUT-DECODE"
EXAMPLE_STDOUT_MISSING = "EXAMPLE-STDOUT-MISSING"
EXAMPLE_STDERR_MISSING = "EXAMPLE-STDERR-MISSING"
EXAMPLE_STDOUT_NOT_EMPTY = "EXAMPLE-STDOUT-NOT-EMPTY"
EXAMPLE_STDERR_NOT_EMPTY = "EXAMPLE-STDERR-NOT-EMPTY"
EXAMPLE_EXCEPTION_TYPE = "EXAMPLE-EXCEPTION-TYPE"
EXAMPLE_EXCEPTION_MESSAGE = "EXAMPLE-EXCEPTION-MESSAGE"
EXAMPLE_CHAPTER_NOT_FOUND = "EXAMPLE-CHAPTER-NOT-FOUND"
EXAMPLE_RECORD_NOT_FOUND = "EXAMPLE-RECORD-NOT-FOUND"

_START_MARKER = "\x00RUNNER_START_ERROR\x00"
_DECODE_MARKER = "\x00RUNNER_DECODE_ERROR:"
_TERMINATE_GRACE_SECONDS = 1.0


class ExampleContractError(ValueError):
    """示例在启动前违反路径或命令契约。"""

    def __init__(self, issues: tuple[Issue, ...]) -> None:
        self.issues = issues
        super().__init__(f"示例执行契约无效，共 {len(issues)} 个问题")


def _issue(record: ExampleRun, code: str, message: str) -> Issue:
    return Issue(code, message, record.source, entity_id=record.example_id)


def _resolve_inside_repo(path: Path, repo_root: Path) -> Path | None:
    candidate = path if path.is_absolute() else repo_root / path
    try:
        resolved = candidate.resolve()
        resolved.relative_to(repo_root.resolve())
    except (OSError, ValueError):
        return None
    return resolved


def _is_python_command(command: str) -> bool:
    executable = Path(command)
    try:
        if executable.is_absolute() and executable.resolve() == Path(sys.executable).resolve():
            return True
    except OSError:
        pass
    return executable.name.lower() in {
        "python", "python.exe", "python3", "python3.exe", "py", "py.exe"
    }


def validate_execution_contract(
    record: ExampleRun, repo_root: Path
) -> tuple[Issue, ...]:
    """校验启动前可判定的路径、输入、命令和超时契约。"""
    root = repo_root.resolve()
    issues: list[Issue] = []

    if not record.command or not _is_python_command(record.command[0]):
        issues.append(
            _issue(record, EXAMPLE_COMMAND_INVALID, "启动命令必须以 Python 解释器占位符开头")
        )
    if not 1 <= record.timeout_seconds <= 30:
        issues.append(
            _issue(record, EXAMPLE_TIMEOUT_INVALID, "超时上限必须在 1..30 秒内")
        )

    source = _resolve_inside_repo(record.source, root)
    if source is None:
        issues.append(
            _issue(record, EXAMPLE_PATH_OUTSIDE_REPO, f"示例入口位于仓库外：{record.source}")
        )
    elif not source.is_file():
        issues.append(
            _issue(record, EXAMPLE_SOURCE_MISSING, f"示例入口不存在：{record.source}")
        )

    working_directory = _resolve_inside_repo(record.working_directory, root)
    if working_directory is None:
        issues.append(
            _issue(
                record,
                EXAMPLE_PATH_OUTSIDE_REPO,
                f"工作目录位于仓库外：{record.working_directory}",
            )
        )
    elif not working_directory.is_dir():
        issues.append(
            _issue(
                record,
                EXAMPLE_WORKDIR_MISSING,
                f"工作目录不存在：{record.working_directory}",
            )
        )

    for input_file in record.input_files:
        resolved_input = _resolve_inside_repo(input_file, root)
        if resolved_input is None:
            issues.append(
                _issue(
                    record,
                    EXAMPLE_PATH_OUTSIDE_REPO,
                    f"输入文件位于仓库外：{input_file}",
                )
            )
        elif not resolved_input.is_file():
            issues.append(
                _issue(record, EXAMPLE_INPUT_MISSING, f"输入文件不存在：{input_file}")
            )
    return sort_issues(issues)


def _decode_output(data: bytes, stream_name: str) -> str:
    try:
        decoded = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        decoded = data.decode("utf-8", errors="replace")
        decoded += f"\n{_DECODE_MARKER}{stream_name}:{error.start}\x00"
    return decoded.replace("\r\n", "\n").replace("\r", "\n")


def run_example(record: ExampleRun, repo_root: Path) -> ExecutionResult:
    """使用当前解释器及参数列表执行一个示例，不通过 shell。"""
    contract_issues = validate_execution_contract(record, repo_root)
    if contract_issues:
        raise ExampleContractError(contract_issues)

    root = repo_root.resolve()
    working_directory = _resolve_inside_repo(record.working_directory, root)
    assert working_directory is not None  # 已由执行契约校验
    command = [sys.executable, *record.command[1:]]
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONPATH"] = str(root)
    started = time.perf_counter()
    try:
        process = subprocess.Popen(
            command,
            cwd=working_directory,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
    except OSError as error:
        duration = time.perf_counter() - started
        message = f"{_START_MARKER}{type(error).__name__}: {error}"
        return ExecutionResult(None, "", message, duration, False)

    timed_out = False
    try:
        stdout_bytes, stderr_bytes = process.communicate(
            timeout=record.timeout_seconds
        )
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        try:
            stdout_bytes, stderr_bytes = process.communicate(
                timeout=_TERMINATE_GRACE_SECONDS
            )
        except subprocess.TimeoutExpired:
            process.kill()
            stdout_bytes, stderr_bytes = process.communicate()

    duration = time.perf_counter() - started
    return ExecutionResult(
        None if timed_out else process.returncode,
        _decode_output(stdout_bytes, "stdout"),
        _decode_output(stderr_bytes, "stderr"),
        duration,
        timed_out,
    )


def _verify_stream(
    record: ExampleRun,
    actual: str,
    expected: tuple[str, ...],
    *,
    missing_code: str,
    not_empty_code: str,
    stream_name: str,
) -> list[Issue]:
    issues: list[Issue] = []
    normalized = actual.replace("\r\n", "\n").replace("\r", "\n")
    if expected and all(fragment == "" for fragment in expected):
        if normalized:
            issues.append(
                _issue(record, not_empty_code, f"预期 {stream_name} 为空，实际产生了输出")
            )
        return issues
    for fragment in expected:
        if fragment and fragment not in normalized:
            issues.append(
                _issue(
                    record,
                    missing_code,
                    f"{stream_name} 缺少 UTF-8 输出片段：{fragment!r}；片段按任意顺序独立匹配",
                )
            )
    return issues


def verify_execution(
    record: ExampleRun, result: ExecutionResult
) -> tuple[Issue, ...]:
    """校验退出码、UTF-8 输出和教学性预期异常，不要求片段顺序。"""
    issues: list[Issue] = []
    for stream_name, output in (("stdout", result.stdout), ("stderr", result.stderr)):
        if _DECODE_MARKER in output:
            issues.append(
                _issue(
                    record,
                    EXAMPLE_OUTPUT_DECODE,
                    f"{stream_name} 不是有效 UTF-8，已用替换字符保留诊断输出",
                )
            )

    if result.timed_out:
        issues.append(
            _issue(
                record,
                EXAMPLE_TIMEOUT,
                f"示例超过 {record.timeout_seconds} 秒，进程已终止",
            )
        )
        return sort_issues(issues)
    if result.exit_code is None:
        detail = result.stderr.removeprefix(_START_MARKER)
        issues.append(
            _issue(record, EXAMPLE_START_FAILED, f"无法启动示例进程：{detail}")
        )
        return sort_issues(issues)

    if result.exit_code != record.expected_exit_code:
        issues.append(
            _issue(
                record,
                EXAMPLE_EXIT_CODE,
                f"预期退出码 {record.expected_exit_code}，实际为 {result.exit_code}",
            )
        )
    issues.extend(
        _verify_stream(
            record,
            result.stdout,
            record.stdout_contains,
            missing_code=EXAMPLE_STDOUT_MISSING,
            not_empty_code=EXAMPLE_STDOUT_NOT_EMPTY,
            stream_name="stdout",
        )
    )
    issues.extend(
        _verify_stream(
            record,
            result.stderr,
            record.stderr_contains,
            missing_code=EXAMPLE_STDERR_MISSING,
            not_empty_code=EXAMPLE_STDERR_NOT_EMPTY,
            stream_name="stderr",
        )
    )

    if record.expected_exception is not None:
        combined = f"{result.stdout}\n{result.stderr}"
        if record.expected_exception.type_name not in combined:
            issues.append(
                _issue(
                    record,
                    EXAMPLE_EXCEPTION_TYPE,
                    f"未输出预期异常类型：{record.expected_exception.type_name}",
                )
            )
        if record.expected_exception.message_contains not in combined:
            issues.append(
                _issue(
                    record,
                    EXAMPLE_EXCEPTION_MESSAGE,
                    f"未输出预期异常消息片段：{record.expected_exception.message_contains}",
                )
            )
    return sort_issues(issues)


def _matches_chapter(selector: str, number: int, chapter_id: str) -> bool:
    normalized = selector.strip().lower()
    return normalized in {
        str(number),
        f"{number:02d}",
        chapter_id.lower(),
    }


def _load_records(
    repo_root: Path,
    chapter_selector: str | None,
    example_selector: str | None,
) -> tuple[list[tuple[str, ExampleRun]], tuple[Issue, ...]]:
    catalog_path = repo_root / "catalog.toml"
    try:
        catalog = load_catalog(catalog_path, repo_root)
    except ContentModelError as error:
        return [], error.issues

    chapters = list(catalog.chapters)
    if chapter_selector is not None:
        chapters = [
            chapter
            for chapter in chapters
            if _matches_chapter(chapter_selector, chapter.number, chapter.chapter_id)
        ]
        if not chapters:
            issue = Issue(
                EXAMPLE_CHAPTER_NOT_FOUND,
                f"找不到章节：{chapter_selector}",
                catalog_path,
                entity_id=chapter_selector,
            )
            return [], (issue,)

    records: list[tuple[str, ExampleRun]] = []
    issues: list[Issue] = []
    for chapter in chapters:
        manifest_path = repo_root / chapter.directory / "chapter.toml"
        try:
            manifest = load_chapter_manifest(manifest_path, repo_root)
        except ContentModelError as error:
            issues.extend(error.issues)
            continue
        for record in manifest.examples:
            if example_selector is None or record.example_id == example_selector:
                records.append((chapter.chapter_id, record))

    if example_selector is not None and not records and not issues:
        issues.append(
            Issue(
                EXAMPLE_RECORD_NOT_FOUND,
                f"所选章节中找不到示例：{example_selector}",
                catalog_path,
                chapter_id=chapters[0].chapter_id if chapters else None,
                entity_id=example_selector,
            )
        )
    return records, sort_issues(issues)


def _format_issue(issue: Issue) -> str:
    context = issue.chapter_id or "-"
    entity = issue.entity_id or "-"
    return f"{issue.code} | {context} | {entity} | {issue.path.as_posix()} | {issue.message}"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="执行并校验章节示例")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--chapter", help="章节编号（如 01）或章节标识（如 CH01）")
    selection.add_argument("--all", action="store_true", help="执行全部章节示例")
    parser.add_argument("--example", help="仅执行指定示例；必须与 --chapter 同用")
    return parser


def main(
    argv: Sequence[str] | None = None, *, repo_root: Path | None = None
) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    if arguments.example is not None and arguments.chapter is None:
        parser.error("--example 必须与 --chapter 同用")

    root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    records, loading_issues = _load_records(
        root,
        arguments.chapter,
        arguments.example,
    )
    all_issues = list(loading_issues)
    for chapter_id, record in records:
        try:
            result = run_example(record, root)
        except ExampleContractError as error:
            all_issues.extend(error.issues)
            continue
        execution_issues = verify_execution(record, result)
        if execution_issues:
            all_issues.extend(execution_issues)
        else:
            print(
                f"PASS | {chapter_id} | {record.example_id} | "
                f"{result.duration_seconds:.3f}s"
            )

    sorted_issues = sort_issues(all_issues)
    for issue in sorted_issues:
        print(_format_issue(issue), file=sys.stderr)
    if sorted_issues:
        print(f"FAIL | {len(sorted_issues)} 个问题", file=sys.stderr)
        return 1
    print(f"OK | 已通过 {len(records)} 个示例")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
