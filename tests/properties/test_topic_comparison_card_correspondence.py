from __future__ import annotations

# Feature: python-learning-for-java-developers, Property 3: 技术主题与对照卡完整对应
# **Validates: Requirements 2.1, 2.6, 2.7, 2.8, 2.9**

from pathlib import Path
from tempfile import TemporaryDirectory

from hypothesis import given, settings, strategies as st

from tools.content_model import (
    CONFIG_DUPLICATE_ID,
    CONFIG_MISSING_FIELD,
    CONFIG_REFERENCE,
    ChapterRef,
    try_load_chapter_manifest,
)
from tools.validate_content import (
    DOC_CODE_FENCE_LANGUAGE,
    DOC_COMPARISON_DUPLICATE,
    DOC_COMPARISON_FIELD_MISSING,
    DOC_COMPARISON_MISSING,
    validate_chapter_template,
    validate_manifest_document,
)


_MUTATIONS = (
    "missing-card",
    "duplicate-card",
    "missing-pitfall",
    "missing-correction",
    "missing-java-approach",
    "missing-python-approach",
    "wrong-java-fence",
    "wrong-python-fence",
)
_CONFIG_EXPECTATIONS = {
    "missing-card": CONFIG_REFERENCE,
    "duplicate-card": CONFIG_DUPLICATE_ID,
    "missing-pitfall": CONFIG_MISSING_FIELD,
    "missing-correction": CONFIG_MISSING_FIELD,
    "missing-java-approach": CONFIG_MISSING_FIELD,
    "missing-python-approach": CONFIG_MISSING_FIELD,
}
_RELEVANT_DOCUMENT_CODES = {
    DOC_COMPARISON_MISSING,
    DOC_COMPARISON_DUPLICATE,
    DOC_COMPARISON_FIELD_MISSING,
    DOC_CODE_FENCE_LANGUAGE,
}


@st.composite
def _comparison_cases(draw: st.DrawFn) -> tuple[list[str], list[bool], str, int]:
    suffixes = draw(
        st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )
    pythonic = draw(st.lists(st.booleans(), min_size=len(suffixes), max_size=len(suffixes)))
    mutation = draw(st.sampled_from(_MUTATIONS))
    target = draw(st.integers(min_value=0, max_value=len(suffixes) - 1))
    return [f"topic-{suffix}" for suffix in suffixes], pythonic, mutation, target


def _card_toml(topic_id: str, pythonic: bool, mutation: str | None = None) -> str:
    lines = [
        "[[comparison_cards]]",
        f'topic_id = "{topic_id}"',
        'shared_purpose = "处理相同业务数据"',
        'observable_difference = "返回值可观察且不同"',
        'python_use_case = "批量数据转换"',
    ]
    if mutation != "missing-pitfall":
        lines.append('java_pitfall = "机械照搬 Java 写法"')
    if mutation != "missing-correction":
        lines.append('correction = "按 Python 对象模型重写"')
    effective_pythonic = pythonic or mutation in {
        "missing-java-approach",
        "missing-python-approach",
    }
    lines.append(f"is_pythonic = {'true' if effective_pythonic else 'false'}")
    if effective_pythonic and mutation != "missing-java-approach":
        lines.append('java_approach = "使用循环累积结果"')
    if effective_pythonic and mutation != "missing-python-approach":
        lines.append('python_approach = "使用推导式生成结果"')
    return "\n".join(lines)


def _manifest_text(
    topic_ids: list[str],
    pythonic: list[bool],
    mutation: str | None = None,
    target: int = 0,
) -> str:
    parts = [
        'chapter_id = "CH01"',
        'requirements = ["2.1", "2.6", "2.7", "2.8", "2.9"]',
    ]
    for topic_id in topic_ids:
        parts.append(
            "\n".join(
                (
                    "[[topics]]",
                    f'topic_id = "{topic_id}"',
                    f'title = "主题 {topic_id}"',
                    f'comparison_anchor = "compare-{topic_id}"',
                    'requirements = ["2.1", "2.6", "2.7", "2.8", "2.9"]',
                )
            )
        )
    for index, (topic_id, is_pythonic) in enumerate(zip(topic_ids, pythonic, strict=True)):
        if mutation == "missing-card" and index == target:
            continue
        card_mutation = mutation if index == target and mutation in _CONFIG_EXPECTATIONS else None
        parts.append(_card_toml(topic_id, is_pythonic, card_mutation))
        if mutation == "duplicate-card" and index == target:
            parts.append(_card_toml(topic_id, is_pythonic))
    parts.extend(
        (
            """[[examples]]
example_id = "example-main"
source = "chapters/01-demo/examples/main.py"
python_spec = ">=3.12,<3.14"
dependencies = []
working_directory = "."
input_preparation = "无需准备"
command = ["python", "chapters/01-demo/examples/main.py"]
timeout_seconds = 5
expected_exit_code = 0
stdout_contains = ["完成"]
stderr_contains = []
requirements = ["2.7"]""",
            '''[[exercises]]
exercise_id = "CH01-EX01"
title = "对照练习"
entry = "chapters/01-demo/exercises/exercise_01.py"
acceptance_id = "ACC-01"
observable_goal = "验证等价结果"''',
            '''[[acceptances]]
acceptance_id = "ACC-01"
exercise_id = "CH01-EX01"
kind = "behavior"
[acceptances.behavior]
input = "相同业务输入"
operation = "分别运行两种实现"
observable_result = "得到相同业务结果"''',
        )
    )
    for topic_id in topic_ids:
        parts.append(
            f'''[[boundaries]]
boundary_id = "{topic_id}-empty"
topic_id = "{topic_id}"
input = "空输入"
expected_behavior = "输出空结果"
requirements = ["2.1"]'''
        )
    for requirement in ("2.1", "2.6", "2.7", "2.8", "2.9"):
        parts.append(
            f'''[[trace_links]]
requirement_id = "{requirement}"
artifact_id = "CH01"'''
        )
    for topic_id in topic_ids:
        parts.append(
            f'''[[trace_links]]
requirement_id = "2.7"
artifact_id = "{topic_id}"
test_id = "equivalent-result-{topic_id}"'''
        )
    return "\n\n".join(parts) + "\n"


def _readme_text(
    topic_ids: list[str], mutation: str | None = None, target: int = 0
) -> str:
    cards: list[str] = []
    for index, topic_id in enumerate(topic_ids):
        java_language = "Java" if mutation == "wrong-java-fence" and index == target else "java"
        python_language = "py" if mutation == "wrong-python-fence" and index == target else "python"
        cards.append(
            f"""### 对照：主题 {topic_id} {{#compare-{topic_id}}}
- 共同用途：处理相同业务数据。
- 可验证行为差异：固定输入的返回值不同。
- Python 适用场景：批量数据转换。
- Java 开发者常见误区：机械照搬 Java 写法。
- 修正方式：按 Python 对象模型重写。
- Java 实现思路：使用循环累积结果。
- Python 实现方式：使用推导式生成相同结果。
- 等价结果验收：[运行测试](#run-example-main)。

```{java_language}
public class Demo {{ public static void main(String[] args) {{ }} }}
```

```{python_language}
def transform(values):
    return [value for value in values]
```"""
        )
    return f"""# 第 1 章：测试章节

## 学习目标
- 能识别主题与对照卡。
- 能修正常见误区。
- 能比较两种实现。

## Java 对照
{'\n\n'.join(cards)}

## Python 知识
对照实现使用相同输入并产生相同业务结果。

## 可运行示例
### 运行记录：example-main {{#run-example-main}}
运行命令后输出完成。

## 练习
- `CH01-EX01`：比较两种实现。

## 验证方式
- `ACC-01`：相同输入产生相同结果。

## 章节总结
每个主题都应有且只有一张完整对照卡。
"""


def _prepare_repository(root: Path) -> tuple[Path, Path]:
    chapter = root / "chapters/01-demo"
    (chapter / "examples").mkdir(parents=True)
    (chapter / "exercises").mkdir()
    (chapter / "examples/main.py").write_text('print("完成")\n', encoding="utf-8")
    (chapter / "exercises/exercise_01.py").write_text("# 练习\n", encoding="utf-8")
    return chapter / "chapter.toml", chapter / "README.md"


@given(case=_comparison_cases())
@settings(max_examples=100, deadline=None)
def test_topics_and_comparison_cards_correspond_completely(
    case: tuple[list[str], list[bool], str, int],
) -> None:
    topic_ids, pythonic, mutation, target = case
    with TemporaryDirectory() as directory:
        root = Path(directory)
        manifest_path, readme_path = _prepare_repository(root)
        manifest_path.write_text(_manifest_text(topic_ids, pythonic), encoding="utf-8")
        readme_path.write_text(_readme_text(topic_ids), encoding="utf-8")

        valid_result = try_load_chapter_manifest(manifest_path, root)
        assert valid_result.value is not None, valid_result.issues
        manifest = valid_result.value
        chapter = ChapterRef(
            1,
            "CH01",
            "测试章节",
            Path("chapters/01-demo"),
            Path("chapters/01-demo/README.md"),
            (),
        )
        document_issues = validate_chapter_template(readme_path, "CH01")
        document_issues += validate_manifest_document(manifest, chapter, readme_path, root)
        assert not ({issue.code for issue in document_issues} & _RELEVANT_DOCUMENT_CODES)

        assert {topic.topic_id for topic in manifest.topics} == {
            card.topic_id for card in manifest.comparison_cards
        }
        assert len(manifest.topics) == len(manifest.comparison_cards)
        for card in manifest.comparison_cards:
            assert card.java_pitfall.strip() and card.correction.strip()
            if card.is_pythonic:
                assert card.java_approach and card.python_approach
                equivalent_links = [
                    link
                    for link in manifest.trace_links
                    if link.artifact_id == card.topic_id
                    and link.requirement_id == "2.7"
                    and link.test_id
                ]
                assert len(equivalent_links) == 1

        manifest_path.write_text(
            _manifest_text(topic_ids, pythonic, mutation, target), encoding="utf-8"
        )
        readme_path.write_text(_readme_text(topic_ids, mutation, target), encoding="utf-8")
        mutated_result = try_load_chapter_manifest(manifest_path, root)
        if mutation in _CONFIG_EXPECTATIONS:
            assert mutated_result.value is None
            assert _CONFIG_EXPECTATIONS[mutation] in {
                issue.code for issue in mutated_result.issues
            }
        else:
            assert mutated_result.value is not None, mutated_result.issues
            fence_issues = validate_chapter_template(readme_path, "CH01")
            assert DOC_CODE_FENCE_LANGUAGE in {issue.code for issue in fence_issues}
