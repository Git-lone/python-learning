from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import textwrap

import pytest

from tools.content_model import (
    CONFIG_DUPLICATE_ID,
    CONFIG_MISSING_FIELD,
    CONFIG_PARSE,
    CONFIG_PATH_OUTSIDE_REPO,
    CONFIG_REFERENCE,
    CONFIG_UNKNOWN_FIELD,
    ContentModelError,
    load_catalog,
    load_chapter_manifest,
    try_load_chapter_manifest,
)


def _write(path: Path, content: str = "占位") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _make_catalog(repo: Path) -> Path:
    _write(repo / "chapters/01-basics/README.md")
    return _write(
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

        [[trace_links]]
        requirement_id = "1.2"
        artifact_id = "CH01"
        """,
    )


def _make_manifest(repo: Path) -> Path:
    _write(repo / "chapters/01-basics/examples/main.py")
    _write(repo / "chapters/01-basics/exercises/exercise_01.py")
    return _write(
        repo / "chapters/01-basics/chapter.toml",
        """
        chapter_id = "CH01"
        requirements = ["1.2", "3.2", "16.5"]

        [[topics]]
        topic_id = "variables"
        title = "变量绑定"
        comparison_anchor = "compare-variables"
        requirements = ["3.2"]

        [[comparison_cards]]
        topic_id = "variables"
        shared_purpose = "保存值"
        observable_difference = "名称可以重新绑定"
        python_use_case = "短生命周期数据处理"
        java_pitfall = "误认为名称类型固定"
        correction = "区分名称与对象"
        is_pythonic = true
        java_approach = "使用局部变量"
        python_approach = "直接绑定名称"

        [[examples]]
        example_id = "basics-main"
        source = "chapters/01-basics/examples/main.py"
        python_spec = ">=3.12,<3.14"
        dependencies = []
        working_directory = "."
        input_preparation = "无需准备"
        command = ["python", "chapters/01-basics/examples/main.py"]
        timeout_seconds = 10
        expected_exit_code = 0
        stdout_contains = ["ok"]
        stderr_contains = []
        requirements = ["3.2"]

        [[boundaries]]
        boundary_id = "variables-empty"
        topic_id = "variables"
        input = "空集合"
        expected_behavior = "输出空结果"
        requirements = ["3.2"]

        [[exercises]]
        exercise_id = "CH01-EX01"
        title = "变量练习"
        entry = "chapters/01-basics/exercises/exercise_01.py"
        acceptance_id = "ACC-01"
        observable_goal = "输出重新绑定结果"

        [[acceptances]]
        acceptance_id = "ACC-01"
        exercise_id = "CH01-EX01"
        kind = "behavior"

        [acceptances.behavior]
        input = "初始名称"
        operation = "重新绑定"
        observable_result = "输出新值"

        [[trace_links]]
        requirement_id = "16.5"
        artifact_id = "CH01-EX01"
        test_id = "test_exercise"
        """,
    )


def test_load_catalog_builds_immutable_catalog(tmp_path: Path) -> None:
    catalog = load_catalog(_make_catalog(tmp_path), tmp_path)

    assert catalog.python_spec == ">=3.12,<3.14"
    assert catalog.chapters[0].number == 1
    assert catalog.chapters[0].entry == Path(
        "chapters/01-basics/README.md"
    )
    assert catalog.trace_links[0].requirement_id == "1.2"
    with pytest.raises(FrozenInstanceError):
        catalog.python_spec = ">=3.14"  # type: ignore[misc]


def test_load_manifest_builds_all_models_and_tuples(tmp_path: Path) -> None:
    manifest = load_chapter_manifest(_make_manifest(tmp_path), tmp_path)

    assert manifest.chapter_id == "CH01"
    assert manifest.topics[0].topic_id == "variables"
    assert manifest.comparison_cards[0].is_pythonic is True
    assert manifest.examples[0].command[0] == "python"
    assert manifest.boundaries[0].expected_behavior == "输出空结果"
    assert manifest.exercises[0].acceptance_id == "ACC-01"
    assert manifest.acceptances[0].behavior is not None
    assert manifest.trace_links[0].artifact_id == "CH01-EX01"
    assert isinstance(manifest.requirements, tuple)
    with pytest.raises(FrozenInstanceError):
        manifest.chapter_id = "CH02"  # type: ignore[misc]


def test_loader_aggregates_and_stably_sorts_independent_issues(
    tmp_path: Path,
) -> None:
    manifest_path = _make_manifest(tmp_path)
    content = manifest_path.read_text(encoding="utf-8")
    content = content.replace(
        'chapter_id = "CH01"',
        'chapter_id = "CH01"\nunknown_root = true',
        1,
    )
    content = content.replace('title = "变量绑定"\n', "", 1)
    content = content.replace(
        'example_id = "basics-main"',
        'example_id = "basics-main"\nsource = "../outside.py"',
        1,
    ).replace(
        'source = "chapters/01-basics/examples/main.py"\n',
        "",
        1,
    )
    duplicate = """
        [[examples]]
        example_id = "basics-main"
        source = "chapters/01-basics/examples/main.py"
        python_spec = ">=3.12,<3.14"
        dependencies = []
        working_directory = "."
        input_preparation = "无需准备"
        command = ["python", "main.py"]
        timeout_seconds = 10
        expected_exit_code = 0
        stdout_contains = ["ok"]
        stderr_contains = []
        requirements = ["3.2"]
    """
    marker = "[[boundaries]]"
    content = content.replace(marker, textwrap.dedent(duplicate) + "\n" + marker)
    manifest_path.write_text(content, encoding="utf-8")

    result = try_load_chapter_manifest(manifest_path, tmp_path)

    assert result.value is None
    codes = {issue.code for issue in result.issues}
    assert {
        CONFIG_UNKNOWN_FIELD,
        CONFIG_MISSING_FIELD,
        CONFIG_PATH_OUTSIDE_REPO,
        CONFIG_DUPLICATE_ID,
    } <= codes
    assert result.issues == tuple(sorted(result.issues, key=lambda issue: issue.sort_key))


def test_toml_parse_error_has_stable_code_and_raises_aggregate_error(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path / "catalog.toml", 'python_spec = "unterminated')

    with pytest.raises(ContentModelError) as raised:
        load_catalog(path, tmp_path)

    assert len(raised.value.issues) == 1
    assert raised.value.issues[0].code == CONFIG_PARSE


def test_exercise_acceptance_bijection_is_validated(tmp_path: Path) -> None:
    path = _make_manifest(tmp_path)
    content = path.read_text(encoding="utf-8").replace(
        'exercise_id = "CH01-EX01"\nkind = "behavior"',
        'exercise_id = "CH01-EX99"\nkind = "behavior"',
    )
    path.write_text(content, encoding="utf-8")

    result = try_load_chapter_manifest(path, tmp_path)

    assert result.value is None
    references = [issue for issue in result.issues if issue.code == CONFIG_REFERENCE]
    assert {issue.entity_id for issue in references} >= {"CH01-EX01", "ACC-01"}
