# Feature: python-learning-for-java-developers, Property 22: 章节模板和练习验收双射

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from hypothesis import given, settings, strategies as st

from tools.content_model import ChapterRef, load_chapter_manifest
from tools.validate_content import SECTIONS, validate_chapter_template, validate_manifest_document

AcceptanceKind = Literal["command", "behavior", "checklist"]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _readme(objective_count: int, kinds: list[AcceptanceKind]) -> str:
    objectives = "\n".join(
        f"- 能通过输出结果验证学习目标 {index}。"
        for index in range(1, objective_count + 1)
    )
    exercises = "\n".join(
        f"- `CH01-EX{index:02d}`：完成练习 {index} 并观察结果。"
        for index in range(1, len(kinds) + 1)
    )
    acceptances = "\n".join(
        f"- `ACC-{index:02d}`：按 {kind} 载荷判定练习结果。"
        for index, kind in enumerate(kinds, 1)
    )
    return f"""# 第 1 章：属性测试章节

## 学习目标
{objectives}

## Java 对照
### 对照：章节结构 {{#compare-structure}}
- 共同用途：组织可验证的学习内容。
- 可验证行为差异：Python 章节使用固定 Markdown 模板。
- Python 适用场景：维护可自动验收的教程。
- Java 开发者常见误区：忽略文档结构约束。
- 修正方式：同时维护文档与机器清单。

## Python 知识
章节结构和清单共同表达学习闭环。

## 可运行示例
### 运行记录：structure-main
从仓库根目录执行示例并观察“完成”。

## 练习
{exercises}

## 验证方式
{acceptances}

## 章节总结
固定模板使每章都具有一致且可验证的学习路径。
"""
def _acceptance_toml(index: int, kind: AcceptanceKind) -> str:
    header = f"""
[[acceptances]]
acceptance_id = "ACC-{index:02d}"
exercise_id = "CH01-EX{index:02d}"
kind = "{kind}"
"""
    if kind == "command":
        return header + f"""
[acceptances.command]
command = ["python", "-m", "pytest", "exercise_{index:02d}.py"]
timeout_seconds = 10
expected_exit_code = 0
expected_output = ["练习 {index} 通过"]
"""
    if kind == "behavior":
        return header + f"""
[acceptances.behavior]
input = "练习 {index} 的固定输入"
operation = "执行练习 {index}"
observable_result = "输出练习 {index} 的结果"
"""
    return header + f"""
[[acceptances.checklist]]
description = "练习 {index} 的结果可观察"
pass_condition = "输出包含练习 {index} 通过"
"""


def _manifest(kinds: list[AcceptanceKind]) -> str:
    exercises = "".join(
        f"""
[[exercises]]
exercise_id = "CH01-EX{index:02d}"
title = "结构练习 {index}"
entry = "chapters/01-property/exercises/exercise_{index:02d}.py"
acceptance_id = "ACC-{index:02d}"
observable_goal = "输出练习 {index} 通过"
"""
        for index in range(1, len(kinds) + 1)
    )
    acceptances = "".join(
        _acceptance_toml(index, kind)
        for index, kind in enumerate(kinds, 1)
    )
    return f"""chapter_id = "CH01"
requirements = []

[[topics]]
topic_id = "structure"
title = "章节结构"
comparison_anchor = "compare-structure"
requirements = []

[[comparison_cards]]
topic_id = "structure"
shared_purpose = "组织内容"
observable_difference = "固定七段模板"
python_use_case = "教程维护"
java_pitfall = "忽略结构"
correction = "同步维护清单"

[[examples]]
example_id = "structure-main"
source = "chapters/01-property/examples/main.py"
python_spec = ">=3.12,<3.14"
dependencies = []
working_directory = "."
input_preparation = "无需准备"
command = ["python", "chapters/01-property/examples/main.py"]
timeout_seconds = 10
expected_exit_code = 0
stdout_contains = ["完成"]
stderr_contains = []
requirements = []

[[boundaries]]
boundary_id = "structure-minimum"
topic_id = "structure"
input = "最小章节"
expected_behavior = "通过结构校验"
requirements = []
{exercises}{acceptances}"""


def _make_chapter(
    repo: Path, objective_count: int, kinds: list[AcceptanceKind]
) -> tuple[Path, Path]:
    chapter = repo / "chapters/01-property"
    readme = chapter / "README.md"
    manifest = chapter / "chapter.toml"
    _write(readme, _readme(objective_count, kinds))
    _write(chapter / "examples/main.py", 'print("完成")\n')
    for index in range(1, len(kinds) + 1):
        _write(
            chapter / f"exercises/exercise_{index:02d}.py",
            f'print("练习 {index} 通过")\n',
        )
    _write(manifest, _manifest(kinds))
    return readme, manifest


chapter_cases = st.tuples(
    st.integers(min_value=3, max_value=5),
    st.lists(
        st.sampled_from(["command", "behavior", "checklist"]),
        min_size=1,
        max_size=3,
    ),
)


@given(chapter_cases)
@settings(max_examples=100, deadline=None)
def test_chapter_template_and_acceptance_bijection(
    case: tuple[int, list[AcceptanceKind]],
) -> None:
    """**Validates: Requirements 16.1-16.10**"""
    objective_count, kinds = case
    with TemporaryDirectory() as temporary_directory:
        repo = Path(temporary_directory)
        readme, manifest_path = _make_chapter(repo, objective_count, kinds)
        text = readme.read_text(encoding="utf-8")

        positions = [text.index(f"## {section}") for section in SECTIONS]
        assert positions == sorted(positions)
        assert all(text.count(f"## {section}") == 1 for section in SECTIONS)
        for index, start in enumerate(positions):
            body_start = text.index("\n", start) + 1
            body_end = positions[index + 1] if index + 1 < len(positions) else len(text)
            assert text[body_start:body_end].strip()
        assert validate_chapter_template(readme, "CH01") == []

        manifest = load_chapter_manifest(manifest_path, repo)
        chapter_ref = ChapterRef(
            1,
            "CH01",
            "属性测试章节",
            Path("chapters/01-property"),
            Path("chapters/01-property/README.md"),
            (),
        )
        assert validate_manifest_document(manifest, chapter_ref, readme, repo) == []

        assert 3 <= objective_count <= 5
        assert 1 <= len(manifest.exercises) <= 3
        exercise_ids = [exercise.exercise_id for exercise in manifest.exercises]
        acceptance_ids = [item.acceptance_id for item in manifest.acceptances]
        assert len(exercise_ids) == len(set(exercise_ids))
        assert len(acceptance_ids) == len(set(acceptance_ids))
        assert {
            exercise.exercise_id: exercise.acceptance_id
            for exercise in manifest.exercises
        } == {
            acceptance.exercise_id: acceptance.acceptance_id
            for acceptance in manifest.acceptances
        }

        for acceptance in manifest.acceptances:
            if acceptance.kind == "command":
                assert acceptance.command is not None
                assert acceptance.command.command[:3] == ("python", "-m", "pytest")
                assert 1 <= acceptance.command.timeout_seconds <= 30
                assert acceptance.command.expected_exit_code == 0
                assert acceptance.command.expected_output
                assert acceptance.behavior is None
                assert acceptance.checklist == ()
            elif acceptance.kind == "behavior":
                assert acceptance.command is None
                assert acceptance.behavior is not None
                assert acceptance.behavior.input
                assert acceptance.behavior.operation
                assert acceptance.behavior.observable_result
                assert acceptance.checklist == ()
            else:
                assert acceptance.command is None
                assert acceptance.behavior is None
                assert acceptance.checklist
                assert all(item.description for item in acceptance.checklist)
                assert all(item.pass_condition for item in acceptance.checklist)
