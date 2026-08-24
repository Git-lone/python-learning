# Feature: python-learning-for-java-developers, Property 4: 示例与运行记录契约完整
# **Validates: Requirements 3.2, 3.4, 3.5, 3.7, 3.15, 3.16**

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TypedDict

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tools.content_model import ChapterRef, load_chapter_manifest
from tools.validate_content import validate_manifest_document


class ContractCase(TypedDict):
    topic_count: int
    example_count: int
    timeouts: list[int]
    exception_flags: list[bool]
    stdout_flags: list[bool]
    empty_output_flags: list[bool]


@st.composite
def contract_cases(draw: st.DrawFn) -> ContractCase:
    topic_count = draw(st.integers(min_value=1, max_value=4))
    example_count = draw(st.integers(min_value=1, max_value=4))
    return {
        "topic_count": topic_count,
        "example_count": example_count,
        "timeouts": draw(
            st.lists(st.integers(min_value=1, max_value=30),
                     min_size=example_count, max_size=example_count)
        ),
        "exception_flags": draw(
            st.lists(st.booleans(), min_size=example_count, max_size=example_count)
        ),
        "stdout_flags": draw(
            st.lists(st.booleans(), min_size=example_count, max_size=example_count)
        ),
        "empty_output_flags": draw(
            st.lists(st.booleans(), min_size=example_count, max_size=example_count)
        ),
    }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _render_manifest(case: ContractCase, chapter_dir: Path) -> str:
    requirements = '["3.2", "3.4", "3.5", "3.7", "3.15", "3.16"]'
    lines = [
        'chapter_id = "CH01"',
        f"requirements = {requirements}",
        "",
    ]
    for index in range(case["topic_count"]):
        topic_id = f"topic-{index}"
        lines.extend([
            "[[topics]]",
            f'topic_id = "{topic_id}"',
            f'title = "主题 {index}"',
            f'comparison_anchor = "compare-{topic_id}"',
            'requirements = ["3.16"]',
            "",
            "[[comparison_cards]]",
            f'topic_id = "{topic_id}"',
            'shared_purpose = "共同用途"',
            'observable_difference = "可观察差异"',
            'python_use_case = "受控场景"',
            'java_pitfall = "常见误区"',
            'correction = "明确修正"',
            "",
        ])
    relative_dir = chapter_dir.as_posix()
    for index in range(case["example_count"]):
        source = f"{relative_dir}/examples/example_{index}.py"
        output = "" if case["empty_output_flags"][index] else f"输出-{index}"
        stdout = f'["{output}"]' if case["stdout_flags"][index] else "[]"
        stderr = "[]" if case["stdout_flags"][index] else f'["{output}"]'
        lines.extend([
            "[[examples]]",
            f'example_id = "example-{index}"',
            f'source = "{source}"',
            'python_spec = ">=3.12,<3.14"',
            "dependencies = []",
            'working_directory = "."',
            'input_preparation = "无需准备"',
            f'command = ["python", "{source}"]',
            f'timeout_seconds = {case["timeouts"][index]}',
            "expected_exit_code = 0",
            f"stdout_contains = {stdout}",
            f"stderr_contains = {stderr}",
            'requirements = ["3.2", "3.4", "3.5", "3.7"]',
        ])
        if case["exception_flags"][index]:
            lines.append(
                'expected_exception = { type_name = "ValueError", '
                'message_contains = "受控异常" }'
            )
        lines.append("")
    for index in range(case["topic_count"]):
        lines.extend([
            "[[boundaries]]",
            f'boundary_id = "boundary-{index}"',
            f'topic_id = "topic-{index}"',
            f'input = "边界输入 {index}"',
            f'expected_behavior = "可观察结果 {index}"',
            'requirements = ["3.16"]',
            "",
        ])
    lines.extend([
        "[[exercises]]",
        'exercise_id = "CH01-EX01"',
        'title = "受控练习"',
        f'entry = "{relative_dir}/exercises/exercise_01.py"',
        'acceptance_id = "ACC-01"',
        'observable_goal = "输出完成"',
        "",
        "[[acceptances]]",
        'acceptance_id = "ACC-01"',
        'exercise_id = "CH01-EX01"',
        'kind = "behavior"',
        'behavior = { input = "固定输入", operation = "执行", '
        'observable_result = "完成" }',
        "",
    ])
    for requirement in ("3.2", "3.4", "3.5", "3.7", "3.15", "3.16"):
        lines.extend([
            "[[trace_links]]",
            f'requirement_id = "{requirement}"',
            'artifact_id = "CH01"',
            "",
        ])
    return "\n".join(lines)


def _render_readme(case: ContractCase) -> str:
    lines = ["# 受控章节", "", "## Java 对照", ""]
    for index in range(case["topic_count"]):
        lines.extend([
            f"### 对照：主题 {index} {{#compare-topic-{index}}}",
            "- 共同用途：共同用途",
            "- 可验证行为差异：可观察差异",
            "- Python 适用场景：受控场景",
            "- Java 开发者常见误区：常见误区",
            "- 修正方式：明确修正",
            "",
        ])
    lines.extend(["## 可运行示例", ""])
    for index in range(case["example_count"]):
        lines.extend([f"### 运行记录：example-{index}", "- 单条非交互命令。", ""])
    return "\n".join(lines)


def _prepare_case(tmp_path: Path, case: ContractCase) -> tuple[Path, ChapterRef]:
    digest = hashlib.sha256(repr(case).encode("utf-8")).hexdigest()[:16]
    relative_dir = Path("generated") / digest / "chapter"
    root = tmp_path / digest
    chapter_root = root / relative_dir
    for index in range(case["example_count"]):
        _write(
            chapter_root / "examples" / f"example_{index}.py",
            "def main() -> int:\n    print('完成')\n    return 0\n\n"
            "if __name__ == '__main__':\n    raise SystemExit(main())\n",
        )
    _write(chapter_root / "exercises" / "exercise_01.py", "# 受控练习\n")
    _write(chapter_root / "README.md", _render_readme(case))
    _write(chapter_root / "chapter.toml", _render_manifest(case, relative_dir))
    chapter = ChapterRef(
        number=1,
        chapter_id="CH01",
        title="受控章节",
        directory=relative_dir,
        entry=relative_dir / "README.md",
        prerequisites=(),
    )
    return root, chapter


@given(case=contract_cases())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_example_and_run_record_contract_is_complete(
    tmp_path: Path, case: ContractCase
) -> None:
    repo_root, chapter = _prepare_case(tmp_path, case)
    manifest_path = repo_root / chapter.directory / "chapter.toml"
    readme = repo_root / chapter.entry
    manifest = load_chapter_manifest(manifest_path, repo_root)

    document_issues = validate_manifest_document(
        manifest, chapter, readme, repo_root
    )
    assert document_issues == []

    discovered = {
        path.resolve().relative_to(repo_root.resolve())
        for path in (repo_root / chapter.directory / "examples").glob("*.py")
        if path.name != "__init__.py"
    }
    recorded = {record.source for record in manifest.examples}
    assert discovered == recorded
    assert len(recorded) == len(manifest.examples)

    for record in manifest.examples:
        assert record.command[0] == "python"
        assert not ({";", "&&", "||", "|"} & set(record.command))
        assert "input(" not in (repo_root / record.source).read_text(encoding="utf-8")
        assert record.stdout_contains or record.stderr_contains
        assert 1 <= record.timeout_seconds <= 30
        if record.expected_exception is not None:
            assert record.expected_exit_code == 0

    topic_ids = {topic.topic_id for topic in manifest.topics}
    covered_topic_ids = {boundary.topic_id for boundary in manifest.boundaries}
    assert topic_ids == covered_topic_ids
