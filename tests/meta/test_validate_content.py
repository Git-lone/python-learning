from __future__ import annotations

from pathlib import Path
import textwrap

import pytest

from tools.content_model import CONFIG_PARSE
from tools.validate_content import (
    CATALOG_DIRECTORY_UNLISTED,
    DOC_CODE_FENCE_LANGUAGE,
    DOC_LINK_MISSING,
    DOC_MANIFEST_MISSING,
    DOC_SECTION_MISSING,
    NAV_CATALOG_MISMATCH,
    TRACE_REQUIREMENT_UNCOVERED,
    main,
    validate_repository,
)


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return path


def _chapter_readme() -> str:
    return """
    # 第 1 章：基础语法

    ## 学习目标
    - 能输出一个绑定值。
    - 能比较 Java 与 Python 实现。
    - 能运行自动验收。

    ## Java 对照
    ### 对照：变量绑定 {#compare-variables}
    - 共同用途：保存值。
    - 可验证行为差异：Python 名称可以重新绑定。
    - Python 适用场景：处理短生命周期数据。
    - Java 开发者常见误区：认为名称类型固定。
    - 修正方式：区分名称与对象。

    ```java
    public class Demo { }
    ```

    ```python
    value = 1
    ```

    ## Python 知识
    名称绑定对象，而不是声明固定槽位。

    ## 可运行示例
    ### 运行记录：basics-main
    从仓库根目录运行 `python chapters/01-basics/examples/main.py`，预期退出码为 0。

    ## 练习
    - `CH01-EX01`：补全变量绑定练习。

    ## 验证方式
    - `ACC-01`：运行后输出 `完成` 即通过。

    ## 章节总结
    本章建立名称与对象的基本心智模型。
    """


def _catalog() -> str:
    return """
    audience = ["具备 Java 基础"]
    python_spec = ">=3.12,<3.14"

    [[chapters]]
    number = 1
    chapter_id = "CH01"
    title = "基础语法"
    directory = "chapters/01-basics"
    entry = "chapters/01-basics/README.md"
    prerequisites = []
    """


def _manifest() -> str:
    return """
    chapter_id = "CH01"
    requirements = ["2.1", "3.2", "16.1", "16.5"]

    [[topics]]
    topic_id = "variables"
    title = "变量绑定"
    comparison_anchor = "compare-variables"
    requirements = ["2.1"]

    [[comparison_cards]]
    topic_id = "variables"
    shared_purpose = "保存值"
    observable_difference = "名称可以重新绑定"
    python_use_case = "数据处理"
    java_pitfall = "名称类型固定"
    correction = "区分名称与对象"

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
    stdout_contains = ["完成"]
    stderr_contains = []
    requirements = ["3.2"]

    [[boundaries]]
    boundary_id = "variables-empty"
    topic_id = "variables"
    input = "空值"
    expected_behavior = "输出空值"
    requirements = ["3.2"]

    [[exercises]]
    exercise_id = "CH01-EX01"
    title = "变量练习"
    entry = "chapters/01-basics/exercises/exercise_01.py"
    acceptance_id = "ACC-01"
    observable_goal = "输出完成"

    [[acceptances]]
    acceptance_id = "ACC-01"
    exercise_id = "CH01-EX01"
    kind = "behavior"

    [acceptances.behavior]
    input = "初始值"
    operation = "重新绑定"
    observable_result = "输出完成"
    """


def _navigation(prefix: str) -> str:
    return f"""
    # 导航

    | 编号 | 主题 | 先修章节 | 唯一入口 |
    |---:|---|---|---|
    | 1 | 基础语法 | 无 | [进入第 1 章]({prefix}chapters/01-basics/README.md) |
    """


def _make_valid_course(repo: Path) -> None:
    _write(repo / "README.md", _navigation(""))
    _write(repo / "INDEX.md", _navigation(""))
    _write(repo / "catalog.toml", _catalog())
    _write(repo / "chapters/01-basics/README.md", _chapter_readme())
    _write(
        repo / "chapters/01-basics/examples/main.py",
        """
        def main() -> int:
            print("完成")
            return 0

        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )
    _write(repo / "chapters/01-basics/exercises/exercise_01.py", "print('完成')")
    manifest = _manifest()
    for requirement in ("2.1", "3.2", "16.1", "16.5"):
        manifest += textwrap.dedent(
            f"""

            [[trace_links]]
            requirement_id = "{requirement}"
            artifact_id = "CH01"
            """
        )
    _write(repo / "chapters/01-basics/chapter.toml", manifest)


def test_valid_repository_passes_all_validation_stages(tmp_path: Path) -> None:
    _make_valid_course(tmp_path)

    assert validate_repository(tmp_path) == ()


def test_mutations_are_located_and_stably_sorted(tmp_path: Path) -> None:
    _make_valid_course(tmp_path)
    readme = tmp_path / "chapters/01-basics/README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        .replace("## 验证方式", "## 验证")
        .replace("```python", "```py")
        + "\n[损坏链接](missing.md)\n",
        encoding="utf-8",
    )
    (tmp_path / "chapters/99-extra").mkdir()
    index = tmp_path / "INDEX.md"
    index.write_text(index.read_text(encoding="utf-8").replace("基础语法", "错误主题"), encoding="utf-8")

    issues = validate_repository(tmp_path)
    codes = {issue.code for issue in issues}

    assert {
        CATALOG_DIRECTORY_UNLISTED,
        DOC_SECTION_MISSING,
        DOC_CODE_FENCE_LANGUAGE,
        DOC_LINK_MISSING,
        NAV_CATALOG_MISMATCH,
    } <= codes
    assert issues == tuple(sorted(issues, key=lambda issue: issue.sort_key))


def test_unparseable_catalog_suppresses_all_dependent_diagnostics(tmp_path: Path) -> None:
    _write(tmp_path / "catalog.toml", 'python_spec = "unterminated')

    issues = validate_repository(tmp_path)

    assert [issue.code for issue in issues] == [CONFIG_PARSE]


def test_unparseable_chapter_manifest_suppresses_manifest_cascades(tmp_path: Path) -> None:
    _make_valid_course(tmp_path)
    _write(tmp_path / "chapters/01-basics/chapter.toml", 'chapter_id = "unterminated')

    issues = validate_repository(tmp_path)

    assert [issue.code for issue in issues] == [CONFIG_PARSE]
    assert issues[0].chapter_id is None


def test_placeholder_chapter_reports_unimplemented_items_explicitly(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", _navigation(""))
    _write(tmp_path / "INDEX.md", _navigation(""))
    _write(tmp_path / "catalog.toml", _catalog())
    _write(
        tmp_path / "chapters/01-basics/README.md",
        """
        # 第 1 章：基础语法

        完整内容将在后续任务中实现。
        """,
    )

    issues = validate_repository(tmp_path)

    assert DOC_MANIFEST_MISSING in {issue.code for issue in issues}
    missing = [issue.entity_id for issue in issues if issue.code == DOC_SECTION_MISSING]
    assert missing == sorted(missing)
    assert set(missing) == {"学习目标", "Java 对照", "Python 知识", "可运行示例", "练习", "验证方式", "章节总结"}


def test_requirement_without_trace_link_is_reported(tmp_path: Path) -> None:
    _make_valid_course(tmp_path)
    manifest = tmp_path / "chapters/01-basics/chapter.toml"
    content = manifest.read_text(encoding="utf-8")
    marker = '[[trace_links]]\nrequirement_id = "16.5"\nartifact_id = "CH01"'
    manifest.write_text(content.replace(marker, ""), encoding="utf-8")

    issues = validate_repository(tmp_path)

    uncovered = [issue for issue in issues if issue.code == TRACE_REQUIREMENT_UNCOVERED]
    assert len(uncovered) == 1
    assert uncovered[0].entity_id == "16.5"


def test_cli_returns_success_and_failure_exit_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_valid_course(tmp_path)
    assert main([], repo_root=tmp_path) == 0
    assert "内容校验通过" in capsys.readouterr().out

    (tmp_path / "chapters/01-basics/chapter.toml").unlink()
    assert main([], repo_root=tmp_path) == 1
    output = capsys.readouterr()
    assert DOC_MANIFEST_MISSING in output.out
    assert "内容校验失败" in output.err
