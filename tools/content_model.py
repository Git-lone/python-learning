"""课程与章节 TOML 清单的不可变模型和严格加载器。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib
from typing import Any, Generic, Literal, TypeVar


CONFIG_PARSE = "CONFIG-PARSE"
CONFIG_MISSING_FIELD = "CONFIG-MISSING-FIELD"
CONFIG_UNKNOWN_FIELD = "CONFIG-UNKNOWN-FIELD"
CONFIG_TYPE = "CONFIG-TYPE"
CONFIG_VALUE = "CONFIG-VALUE"
CONFIG_DUPLICATE_ID = "CONFIG-DUPLICATE-ID"
CONFIG_DUPLICATE_NUMBER = "CONFIG-DUPLICATE-NUMBER"
CONFIG_DUPLICATE_PATH = "CONFIG-DUPLICATE-PATH"
CONFIG_PATH_OUTSIDE_REPO = "CONFIG-PATH-OUTSIDE-REPO"
CONFIG_PATH_NOT_FOUND = "CONFIG-PATH-NOT-FOUND"
CONFIG_REFERENCE = "CONFIG-REFERENCE"
CONFIG_UNKNOWN_REQUIREMENT = "CONFIG-UNKNOWN-REQUIREMENT"

_REQUIREMENT_ID = re.compile(r"^(\d+)\.(\d+)$")
_REQUIREMENT_MAX = {
    1: 10, 2: 9, 3: 16, 4: 13, 5: 12, 6: 14, 7: 12, 8: 10,
    9: 13, 10: 14, 11: 12, 12: 13, 13: 18, 14: 16, 15: 23, 16: 17,
}


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    path: Path
    chapter_id: str | None = None
    entity_id: str | None = None

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return (self.path.as_posix(), self.code, self.entity_id or "")


@dataclass(frozen=True)
class TraceLink:
    requirement_id: str
    artifact_id: str
    test_id: str | None = None


@dataclass(frozen=True)
class ChapterRef:
    number: int
    chapter_id: str
    title: str
    directory: Path
    entry: Path
    prerequisites: tuple[int, ...]


@dataclass(frozen=True)
class CourseCatalog:
    audience: tuple[str, ...]
    python_spec: str
    chapters: tuple[ChapterRef, ...]
    trace_links: tuple[TraceLink, ...] = ()


@dataclass(frozen=True)
class Topic:
    topic_id: str
    title: str
    comparison_anchor: str
    requirements: tuple[str, ...]


@dataclass(frozen=True)
class ComparisonCard:
    topic_id: str
    shared_purpose: str
    observable_difference: str
    python_use_case: str
    java_pitfall: str
    correction: str
    java_approach: str | None = None
    python_approach: str | None = None
    is_pythonic: bool = False


@dataclass(frozen=True)
class ExpectedException:
    type_name: str
    message_contains: str


@dataclass(frozen=True)
class ExampleRun:
    example_id: str
    source: Path
    python_spec: str
    dependencies: tuple[str, ...]
    working_directory: Path
    input_preparation: str
    command: tuple[str, ...]
    timeout_seconds: int
    expected_exit_code: int
    stdout_contains: tuple[str, ...]
    stderr_contains: tuple[str, ...]
    expected_exception: ExpectedException | None
    requirements: tuple[str, ...]
    input_files: tuple[Path, ...] = ()


@dataclass(frozen=True)
class BoundaryCase:
    boundary_id: str
    topic_id: str
    input: str
    expected_behavior: str
    requirements: tuple[str, ...]


@dataclass(frozen=True)
class Exercise:
    exercise_id: str
    title: str
    entry: Path
    acceptance_id: str
    observable_goal: str


@dataclass(frozen=True)
class CommandExpectation:
    command: tuple[str, ...]
    timeout_seconds: int
    expected_exit_code: int
    expected_output: tuple[str, ...]


@dataclass(frozen=True)
class BehaviorExpectation:
    input: str
    operation: str
    observable_result: str


@dataclass(frozen=True)
class ChecklistItem:
    description: str
    pass_condition: str


AcceptanceKind = Literal["command", "behavior", "checklist"]


@dataclass(frozen=True)
class Acceptance:
    acceptance_id: str
    exercise_id: str
    kind: AcceptanceKind
    command: CommandExpectation | None = None
    behavior: BehaviorExpectation | None = None
    checklist: tuple[ChecklistItem, ...] = ()


@dataclass(frozen=True)
class ChapterManifest:
    chapter_id: str
    requirements: tuple[str, ...]
    topics: tuple[Topic, ...]
    comparison_cards: tuple[ComparisonCard, ...]
    examples: tuple[ExampleRun, ...]
    boundaries: tuple[BoundaryCase, ...]
    exercises: tuple[Exercise, ...]
    acceptances: tuple[Acceptance, ...]
    trace_links: tuple[TraceLink, ...] = ()


@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool


T = TypeVar("T")


@dataclass(frozen=True)
class LoadResult(Generic[T]):
    value: T | None
    issues: tuple[Issue, ...]

    @property
    def ok(self) -> bool:
        return self.value is not None and not self.issues


class ContentModelError(ValueError):
    """清单包含一个或多个问题。"""

    def __init__(self, issues: tuple[Issue, ...]) -> None:
        self.issues = issues
        super().__init__(f"清单校验失败，共 {len(issues)} 个问题")


def sort_issues(issues: list[Issue] | tuple[Issue, ...]) -> tuple[Issue, ...]:
    return tuple(sorted(issues, key=lambda issue: issue.sort_key))


class _Reader:
    def __init__(
        self,
        data: dict[str, Any],
        *,
        source: Path,
        issues: list[Issue],
        context: str,
        chapter_id: str | None = None,
        entity_id: str | None = None,
    ) -> None:
        self.data = data
        self.source = source
        self.issues = issues
        self.context = context
        self.chapter_id = chapter_id
        self.entity_id = entity_id

    def check_keys(self, required: set[str], optional: set[str] = set()) -> None:
        for key in sorted(required - self.data.keys()):
            self.add(CONFIG_MISSING_FIELD, f"{self.context} 缺少字段“{key}”")
        for key in sorted(self.data.keys() - required - optional):
            self.add(CONFIG_UNKNOWN_FIELD, f"{self.context} 包含未知字段“{key}”")

    def add(self, code: str, message: str) -> None:
        self.issues.append(
            Issue(code, message, self.source, self.chapter_id, self.entity_id)
        )

    def string(self, key: str, *, allow_empty: bool = False) -> str:
        value = self.data.get(key)
        if not isinstance(value, str):
            if key in self.data:
                self.add(CONFIG_TYPE, f"{self.context}.{key} 必须是字符串")
            return ""
        if not allow_empty and not value.strip():
            self.add(CONFIG_VALUE, f"{self.context}.{key} 不得为空")
        return value

    def optional_string(self, key: str) -> str | None:
        if key not in self.data:
            return None
        value = self.data[key]
        if not isinstance(value, str):
            self.add(CONFIG_TYPE, f"{self.context}.{key} 必须是字符串")
            return None
        if not value.strip():
            self.add(CONFIG_VALUE, f"{self.context}.{key} 不得为空")
        return value

    def integer(self, key: str) -> int:
        value = self.data.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            if key in self.data:
                self.add(CONFIG_TYPE, f"{self.context}.{key} 必须是整数")
            return 0
        return value

    def boolean(self, key: str, default: bool = False) -> bool:
        if key not in self.data:
            return default
        value = self.data[key]
        if not isinstance(value, bool):
            self.add(CONFIG_TYPE, f"{self.context}.{key} 必须是布尔值")
            return default
        return value

    def strings(self, key: str, *, allow_empty: bool = True) -> tuple[str, ...]:
        value = self.data.get(key)
        if not isinstance(value, list):
            if key in self.data:
                self.add(CONFIG_TYPE, f"{self.context}.{key} 必须是字符串数组")
            return ()
        result: list[str] = []
        for index, item in enumerate(value):
            if not isinstance(item, str):
                self.add(CONFIG_TYPE, f"{self.context}.{key}[{index}] 必须是字符串")
            elif not allow_empty and not item.strip():
                self.add(CONFIG_VALUE, f"{self.context}.{key}[{index}] 不得为空")
            else:
                result.append(item)
        return tuple(result)

    def integers(self, key: str) -> tuple[int, ...]:
        value = self.data.get(key)
        if not isinstance(value, list):
            if key in self.data:
                self.add(CONFIG_TYPE, f"{self.context}.{key} 必须是整数数组")
            return ()
        result: list[int] = []
        for index, item in enumerate(value):
            if isinstance(item, bool) or not isinstance(item, int):
                self.add(CONFIG_TYPE, f"{self.context}.{key}[{index}] 必须是整数")
            else:
                result.append(item)
        return tuple(result)

    def table(self, key: str) -> dict[str, Any] | None:
        if key not in self.data:
            return None
        value = self.data[key]
        if not isinstance(value, dict):
            self.add(CONFIG_TYPE, f"{self.context}.{key} 必须是表")
            return None
        return value


def _table_items(
    root: _Reader, key: str, *, required: bool = True
) -> list[dict[str, Any]]:
    value = root.data.get(key)
    if value is None:
        if required:
            root.add(CONFIG_MISSING_FIELD, f"{root.context} 缺少字段“{key}”")
        return []
    if not isinstance(value, list):
        root.add(CONFIG_TYPE, f"{root.context}.{key} 必须是表数组")
        return []
    tables: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if isinstance(item, dict):
            tables.append(item)
        else:
            root.add(CONFIG_TYPE, f"{root.context}.{key}[{index}] 必须是表")
    return tables


def _find_repo_root(source: Path) -> Path:
    start = source.resolve().parent
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return start


def _read_toml(source: Path, issues: list[Issue]) -> dict[str, Any] | None:
    try:
        with source.open("rb") as stream:
            value = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as error:
        issues.append(Issue(CONFIG_PARSE, f"无法解析 TOML：{error}", source))
        return None
    return value


def _path_value(
    reader: _Reader,
    key: str,
    repo_root: Path,
    *,
    must_exist: bool,
    directory: bool = False,
) -> Path:
    raw = reader.string(key)
    if not raw:
        return Path()
    configured = Path(raw)
    candidate = configured if configured.is_absolute() else repo_root / configured
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(repo_root.resolve())
    except ValueError:
        reader.add(
            CONFIG_PATH_OUTSIDE_REPO,
            f"{reader.context}.{key} 指向仓库外路径：{raw}",
        )
        return configured
    if must_exist and not resolved.exists():
        reader.add(CONFIG_PATH_NOT_FOUND, f"{reader.context}.{key} 路径不存在：{raw}")
    elif must_exist and directory and not resolved.is_dir():
        reader.add(CONFIG_VALUE, f"{reader.context}.{key} 必须指向目录：{raw}")
    elif must_exist and not directory and not resolved.is_file():
        reader.add(CONFIG_VALUE, f"{reader.context}.{key} 必须指向文件：{raw}")
    return relative


def _requirements(reader: _Reader, key: str = "requirements") -> tuple[str, ...]:
    values = reader.strings(key, allow_empty=False)
    for value in values:
        match = _REQUIREMENT_ID.fullmatch(value)
        if match is None:
            reader.add(CONFIG_UNKNOWN_REQUIREMENT, f"未知需求标识：{value}")
            continue
        group, criterion = (int(part) for part in match.groups())
        if group not in _REQUIREMENT_MAX or not 1 <= criterion <= _REQUIREMENT_MAX[group]:
            reader.add(CONFIG_UNKNOWN_REQUIREMENT, f"未知需求标识：{value}")
    return values


def _reader(
    data: dict[str, Any],
    root: _Reader,
    context: str,
    *,
    chapter_id: str | None = None,
    entity_id: str | None = None,
) -> _Reader:
    return _Reader(
        data,
        source=root.source,
        issues=root.issues,
        context=context,
        chapter_id=chapter_id if chapter_id is not None else root.chapter_id,
        entity_id=entity_id,
    )


def _report_duplicates(
    values: list[tuple[object, str | None]],
    *,
    root: _Reader,
    label: str,
    code: str = CONFIG_DUPLICATE_ID,
) -> None:
    seen: set[object] = set()
    reported: set[object] = set()
    for value, entity_id in values:
        if value in seen and value not in reported:
            root.issues.append(
                Issue(
                    code,
                    f"{label} 重复：{value}",
                    root.source,
                    root.chapter_id,
                    entity_id,
                )
            )
            reported.add(value)
        seen.add(value)


def _parse_trace_links(root: _Reader, chapter_id: str | None) -> tuple[TraceLink, ...]:
    links: list[TraceLink] = []
    for index, data in enumerate(_table_items(root, "trace_links", required=False)):
        item = _reader(data, root, f"trace_links[{index}]", chapter_id=chapter_id)
        item.check_keys({"requirement_id", "artifact_id"}, {"test_id"})
        requirement_id = item.string("requirement_id")
        artifact_id = item.string("artifact_id")
        test_id = item.optional_string("test_id")
        if requirement_id:
            probe = _Reader(
                {"requirements": [requirement_id]}, source=root.source,
                issues=root.issues, context=item.context, chapter_id=chapter_id,
                entity_id=artifact_id or None,
            )
            _requirements(probe)
        links.append(TraceLink(requirement_id, artifact_id, test_id))
    return tuple(links)


def try_load_catalog(path: Path, repo_root: Path | None = None) -> LoadResult[CourseCatalog]:
    source = path.resolve()
    issues: list[Issue] = []
    data = _read_toml(source, issues)
    if data is None:
        return LoadResult(None, sort_issues(issues))
    root_path = (repo_root or _find_repo_root(source)).resolve()
    root = _Reader(data, source=source, issues=issues, context="catalog")
    root.check_keys({"audience", "python_spec", "chapters"}, {"trace_links"})
    audience = root.strings("audience", allow_empty=False)
    python_spec = root.string("python_spec")
    chapters: list[ChapterRef] = []
    for index, chapter_data in enumerate(_table_items(root, "chapters", required=False)):
        context = f"chapters[{index}]"
        chapter_id_hint = chapter_data.get("chapter_id")
        chapter_id = chapter_id_hint if isinstance(chapter_id_hint, str) else None
        item = _reader(chapter_data, root, context, chapter_id=chapter_id)
        item.check_keys(
            {"number", "chapter_id", "title", "directory", "entry", "prerequisites"}
        )
        number = item.integer("number")
        parsed_id = item.string("chapter_id")
        title = item.string("title")
        directory_path = _path_value(
            item, "directory", root_path, must_exist=True, directory=True
        )
        entry = _path_value(item, "entry", root_path, must_exist=True)
        prerequisites = item.integers("prerequisites")
        if number < 1:
            item.add(CONFIG_VALUE, f"{context}.number 必须大于等于 1")
        for prerequisite in prerequisites:
            if prerequisite >= number:
                item.add(
                    CONFIG_REFERENCE,
                    f"{context}.prerequisites 只能引用较早章节：{prerequisite}",
                )
        if len(set(prerequisites)) != len(prerequisites):
            item.add(CONFIG_DUPLICATE_ID, f"{context}.prerequisites 包含重复编号")
        if directory_path != Path() and entry != Path():
            try:
                entry.relative_to(directory_path)
            except ValueError:
                item.add(CONFIG_REFERENCE, f"{context}.entry 不在章节目录内")
        chapters.append(
            ChapterRef(number, parsed_id, title, directory_path, entry, prerequisites)
        )
    trace_links = _parse_trace_links(root, None)
    _validate_catalog(chapters, trace_links, root)
    catalog = CourseCatalog(audience, python_spec, tuple(chapters), trace_links)
    sorted_issues = sort_issues(issues)
    return LoadResult(catalog if not sorted_issues else None, sorted_issues)


def _validate_catalog(
    chapters: list[ChapterRef], trace_links: tuple[TraceLink, ...], root: _Reader
) -> None:
    _report_duplicates(
        [(chapter.chapter_id, chapter.chapter_id) for chapter in chapters],
        root=root,
        label="章节标识",
    )
    _report_duplicates(
        [(chapter.number, chapter.chapter_id) for chapter in chapters],
        root=root,
        label="章节编号",
        code=CONFIG_DUPLICATE_NUMBER,
    )
    _report_duplicates(
        [(chapter.directory.as_posix(), chapter.chapter_id) for chapter in chapters],
        root=root,
        label="章节目录",
        code=CONFIG_DUPLICATE_PATH,
    )
    _report_duplicates(
        [(chapter.entry.as_posix(), chapter.chapter_id) for chapter in chapters],
        root=root,
        label="章节入口",
        code=CONFIG_DUPLICATE_PATH,
    )
    numbers = [chapter.number for chapter in chapters]
    if numbers != list(range(1, len(chapters) + 1)):
        root.add(CONFIG_VALUE, "章节编号必须按 TOML 顺序从 1 连续递增")
    number_set = set(numbers)
    for chapter in chapters:
        for prerequisite in chapter.prerequisites:
            if prerequisite not in number_set:
                root.issues.append(
                    Issue(
                        CONFIG_REFERENCE,
                        f"先修章节不存在：{prerequisite}",
                        root.source,
                        chapter.chapter_id,
                        str(prerequisite),
                    )
                )
    artifact_ids = {chapter.chapter_id for chapter in chapters}
    for link in trace_links:
        if link.artifact_id not in artifact_ids:
            root.issues.append(
                Issue(
                    CONFIG_REFERENCE,
                    f"追踪工件不存在：{link.artifact_id}",
                    root.source,
                    entity_id=link.artifact_id,
                )
            )


def load_catalog(path: Path, repo_root: Path | None = None) -> CourseCatalog:
    result = try_load_catalog(path, repo_root)
    if result.value is None:
        raise ContentModelError(result.issues)
    return result.value


def _parse_topics(root: _Reader, chapter_id: str) -> tuple[Topic, ...]:
    topics: list[Topic] = []
    for index, data in enumerate(_table_items(root, "topics", required=False)):
        hint = data.get("topic_id")
        entity_id = hint if isinstance(hint, str) else None
        item = _reader(
            data, root, f"topics[{index}]", chapter_id=chapter_id, entity_id=entity_id
        )
        item.check_keys({"topic_id", "title", "comparison_anchor", "requirements"})
        topics.append(
            Topic(
                item.string("topic_id"),
                item.string("title"),
                item.string("comparison_anchor"),
                _requirements(item),
            )
        )
    return tuple(topics)


def _parse_cards(root: _Reader, chapter_id: str) -> tuple[ComparisonCard, ...]:
    cards: list[ComparisonCard] = []
    required = {
        "topic_id", "shared_purpose", "observable_difference", "python_use_case",
        "java_pitfall", "correction",
    }
    optional = {"java_approach", "python_approach", "is_pythonic"}
    for index, data in enumerate(_table_items(root, "comparison_cards", required=False)):
        hint = data.get("topic_id")
        topic_id = hint if isinstance(hint, str) else None
        item = _reader(
            data, root, f"comparison_cards[{index}]",
            chapter_id=chapter_id, entity_id=topic_id,
        )
        item.check_keys(required, optional)
        parsed_topic_id = item.string("topic_id")
        java_approach = item.optional_string("java_approach")
        python_approach = item.optional_string("python_approach")
        is_pythonic = item.boolean("is_pythonic")
        if (java_approach is None) != (python_approach is None):
            item.add(CONFIG_VALUE, "Java 思路与 Python 实现必须同时提供")
        if is_pythonic and (java_approach is None or python_approach is None):
            item.add(CONFIG_MISSING_FIELD, "Python 惯用法对照卡必须提供两种实现")
        cards.append(
            ComparisonCard(
                parsed_topic_id,
                item.string("shared_purpose"),
                item.string("observable_difference"),
                item.string("python_use_case"),
                item.string("java_pitfall"),
                item.string("correction"),
                java_approach,
                python_approach,
                is_pythonic,
            )
        )
    return tuple(cards)


def _parse_expected_exception(
    item: _Reader, chapter_id: str, example_id: str
) -> ExpectedException | None:
    data = item.table("expected_exception")
    if data is None:
        return None
    nested = _reader(
        data, item, f"{item.context}.expected_exception",
        chapter_id=chapter_id, entity_id=example_id,
    )
    nested.check_keys({"type_name", "message_contains"})
    return ExpectedException(
        nested.string("type_name"), nested.string("message_contains")
    )


def _parse_examples(
    root: _Reader, chapter_id: str, repo_root: Path
) -> tuple[ExampleRun, ...]:
    examples: list[ExampleRun] = []
    required = {
        "example_id", "source", "python_spec", "dependencies", "working_directory",
        "input_preparation", "command", "timeout_seconds", "expected_exit_code",
        "stdout_contains", "stderr_contains", "requirements",
    }
    optional = {"expected_exception", "input_files"}
    for index, data in enumerate(_table_items(root, "examples", required=False)):
        hint = data.get("example_id")
        example_id = hint if isinstance(hint, str) else None
        item = _reader(
            data, root, f"examples[{index}]",
            chapter_id=chapter_id, entity_id=example_id,
        )
        item.check_keys(required, optional)
        parsed_id = item.string("example_id")
        source = _path_value(item, "source", repo_root, must_exist=True)
        working_directory = _path_value(
            item, "working_directory", repo_root, must_exist=True, directory=True
        )
        command = item.strings("command", allow_empty=False)
        timeout = item.integer("timeout_seconds")
        expected_exit_code = item.integer("expected_exit_code")
        stdout = item.strings("stdout_contains")
        stderr = item.strings("stderr_contains")
        input_files = _parse_input_files(item, repo_root)
        expected_exception = _parse_expected_exception(item, chapter_id, parsed_id)
        if not command:
            item.add(CONFIG_VALUE, f"{item.context}.command 必须包含一条参数化命令")
        if not 1 <= timeout <= 30:
            item.add(CONFIG_VALUE, f"{item.context}.timeout_seconds 必须在 1..30 内")
        if not stdout and not stderr:
            item.add(CONFIG_VALUE, f"{item.context} 必须声明至少一个输出期望")
        if expected_exception is not None and expected_exit_code != 0:
            item.add(CONFIG_VALUE, "预期异常示例的 expected_exit_code 必须为 0")
        examples.append(
            ExampleRun(
                parsed_id, source, item.string("python_spec"),
                item.strings("dependencies", allow_empty=False), working_directory,
                item.string("input_preparation", allow_empty=True), command, timeout,
                expected_exit_code, stdout, stderr, expected_exception,
                _requirements(item), input_files,
            )
        )
    return tuple(examples)


def _parse_input_files(item: _Reader, repo_root: Path) -> tuple[Path, ...]:
    if "input_files" not in item.data:
        return ()
    raw_values = item.strings("input_files", allow_empty=False)
    paths: list[Path] = []
    for index, raw in enumerate(raw_values):
        probe = _Reader(
            {"value": raw}, source=item.source, issues=item.issues,
            context=f"{item.context}.input_files[{index}]",
            chapter_id=item.chapter_id, entity_id=item.entity_id,
        )
        paths.append(_path_value(probe, "value", repo_root, must_exist=True))
    return tuple(paths)


def _parse_boundaries(root: _Reader, chapter_id: str) -> tuple[BoundaryCase, ...]:
    boundaries: list[BoundaryCase] = []
    for index, data in enumerate(_table_items(root, "boundaries", required=False)):
        hint = data.get("boundary_id")
        boundary_id = hint if isinstance(hint, str) else None
        item = _reader(
            data, root, f"boundaries[{index}]",
            chapter_id=chapter_id, entity_id=boundary_id,
        )
        item.check_keys(
            {"boundary_id", "topic_id", "input", "expected_behavior", "requirements"}
        )
        boundaries.append(
            BoundaryCase(
                item.string("boundary_id"), item.string("topic_id"),
                item.string("input", allow_empty=True), item.string("expected_behavior"),
                _requirements(item),
            )
        )
    return tuple(boundaries)


def _parse_exercises(
    root: _Reader, chapter_id: str, repo_root: Path
) -> tuple[Exercise, ...]:
    exercises: list[Exercise] = []
    for index, data in enumerate(_table_items(root, "exercises", required=False)):
        hint = data.get("exercise_id")
        exercise_id = hint if isinstance(hint, str) else None
        item = _reader(
            data, root, f"exercises[{index}]",
            chapter_id=chapter_id, entity_id=exercise_id,
        )
        item.check_keys(
            {"exercise_id", "title", "entry", "acceptance_id", "observable_goal"}
        )
        exercises.append(
            Exercise(
                item.string("exercise_id"), item.string("title"),
                _path_value(item, "entry", repo_root, must_exist=True),
                item.string("acceptance_id"), item.string("observable_goal"),
            )
        )
    return tuple(exercises)


def _parse_command_expectation(item: _Reader) -> CommandExpectation | None:
    data = item.table("command")
    if data is None:
        return None
    nested = _reader(
        data, item, f"{item.context}.command",
        chapter_id=item.chapter_id, entity_id=item.entity_id,
    )
    nested.check_keys(
        {"command", "timeout_seconds", "expected_exit_code", "expected_output"}
    )
    command = nested.strings("command", allow_empty=False)
    timeout = nested.integer("timeout_seconds")
    output = nested.strings("expected_output")
    if not command:
        nested.add(CONFIG_VALUE, f"{nested.context}.command 不得为空")
    if not 1 <= timeout <= 30:
        nested.add(CONFIG_VALUE, f"{nested.context}.timeout_seconds 必须在 1..30 内")
    if not output:
        nested.add(CONFIG_VALUE, f"{nested.context}.expected_output 必须包含输出期望")
    return CommandExpectation(
        command, timeout, nested.integer("expected_exit_code"), output
    )


def _parse_behavior_expectation(item: _Reader) -> BehaviorExpectation | None:
    data = item.table("behavior")
    if data is None:
        return None
    nested = _reader(
        data, item, f"{item.context}.behavior",
        chapter_id=item.chapter_id, entity_id=item.entity_id,
    )
    nested.check_keys({"input", "operation", "observable_result"})
    return BehaviorExpectation(
        nested.string("input", allow_empty=True), nested.string("operation"),
        nested.string("observable_result"),
    )


def _parse_checklist(item: _Reader) -> tuple[ChecklistItem, ...]:
    data = item.data.get("checklist")
    if data is None:
        return ()
    if not isinstance(data, list):
        item.add(CONFIG_TYPE, f"{item.context}.checklist 必须是表数组")
        return ()
    result: list[ChecklistItem] = []
    for index, raw in enumerate(data):
        if not isinstance(raw, dict):
            item.add(CONFIG_TYPE, f"{item.context}.checklist[{index}] 必须是表")
            continue
        nested = _reader(
            raw, item, f"{item.context}.checklist[{index}]",
            chapter_id=item.chapter_id, entity_id=item.entity_id,
        )
        nested.check_keys({"description", "pass_condition"})
        result.append(
            ChecklistItem(nested.string("description"), nested.string("pass_condition"))
        )
    return tuple(result)


def _parse_acceptances(root: _Reader, chapter_id: str) -> tuple[Acceptance, ...]:
    acceptances: list[Acceptance] = []
    for index, data in enumerate(_table_items(root, "acceptances", required=False)):
        hint = data.get("acceptance_id")
        acceptance_id = hint if isinstance(hint, str) else None
        item = _reader(
            data, root, f"acceptances[{index}]",
            chapter_id=chapter_id, entity_id=acceptance_id,
        )
        item.check_keys(
            {"acceptance_id", "exercise_id", "kind"},
            {"command", "behavior", "checklist"},
        )
        parsed_id = item.string("acceptance_id")
        exercise_id = item.string("exercise_id")
        raw_kind = item.string("kind")
        kind: AcceptanceKind = "command"
        if raw_kind in {"command", "behavior", "checklist"}:
            kind = raw_kind  # type: ignore[assignment]
        elif raw_kind:
            item.add(CONFIG_VALUE, f"{item.context}.kind 必须是 command、behavior 或 checklist")
        command = _parse_command_expectation(item)
        behavior = _parse_behavior_expectation(item)
        checklist = _parse_checklist(item)
        present = {
            "command": command is not None,
            "behavior": behavior is not None,
            "checklist": "checklist" in data,
        }
        if raw_kind in present and not present[raw_kind]:
            item.add(CONFIG_MISSING_FIELD, f"{item.context} 缺少 {raw_kind} 载荷")
        for payload, exists in present.items():
            if exists and payload != raw_kind:
                item.add(CONFIG_VALUE, f"{item.context} 包含与 kind 不匹配的 {payload} 载荷")
        if raw_kind == "checklist" and not checklist:
            item.add(CONFIG_VALUE, f"{item.context}.checklist 不得为空")
        acceptances.append(
            Acceptance(parsed_id, exercise_id, kind, command, behavior, checklist)
        )
    return tuple(acceptances)


def try_load_chapter_manifest(
    path: Path, repo_root: Path | None = None
) -> LoadResult[ChapterManifest]:
    source = path.resolve()
    issues: list[Issue] = []
    data = _read_toml(source, issues)
    if data is None:
        return LoadResult(None, sort_issues(issues))
    root_path = (repo_root or _find_repo_root(source)).resolve()
    chapter_hint = data.get("chapter_id")
    chapter_id_hint = chapter_hint if isinstance(chapter_hint, str) else None
    root = _Reader(
        data, source=source, issues=issues, context="chapter",
        chapter_id=chapter_id_hint,
    )
    root.check_keys(
        {
            "chapter_id", "requirements", "topics", "comparison_cards", "examples",
            "boundaries", "exercises", "acceptances",
        },
        {"trace_links"},
    )
    chapter_id = root.string("chapter_id")
    requirements = _requirements(root)
    topics = _parse_topics(root, chapter_id)
    cards = _parse_cards(root, chapter_id)
    examples = _parse_examples(root, chapter_id, root_path)
    boundaries = _parse_boundaries(root, chapter_id)
    exercises = _parse_exercises(root, chapter_id, root_path)
    acceptances = _parse_acceptances(root, chapter_id)
    trace_links = _parse_trace_links(root, chapter_id)
    manifest = ChapterManifest(
        chapter_id, requirements, topics, cards, examples, boundaries,
        exercises, acceptances, trace_links,
    )
    _validate_manifest(manifest, root)
    sorted_issues = sort_issues(issues)
    return LoadResult(manifest if not sorted_issues else None, sorted_issues)


def _validate_manifest(manifest: ChapterManifest, root: _Reader) -> None:
    groups: tuple[tuple[str, list[tuple[object, str | None]]], ...] = (
        ("主题标识", [(value.topic_id, value.topic_id) for value in manifest.topics]),
        ("对照卡主题标识", [(value.topic_id, value.topic_id) for value in manifest.comparison_cards]),
        ("示例标识", [(value.example_id, value.example_id) for value in manifest.examples]),
        ("边界标识", [(value.boundary_id, value.boundary_id) for value in manifest.boundaries]),
        ("练习标识", [(value.exercise_id, value.exercise_id) for value in manifest.exercises]),
        ("验收标识", [(value.acceptance_id, value.acceptance_id) for value in manifest.acceptances]),
    )
    for label, values in groups:
        _report_duplicates(values, root=root, label=label)
    _report_duplicates(
        [(value.source.as_posix(), value.example_id) for value in manifest.examples],
        root=root, label="示例路径", code=CONFIG_DUPLICATE_PATH,
    )
    if not manifest.examples:
        root.add(CONFIG_MISSING_FIELD, "章节必须提供至少一个示例运行记录")
    _validate_topic_links(manifest, root)
    _validate_exercise_links(manifest, root)
    _validate_trace_links(manifest, root)


def _validate_topic_links(manifest: ChapterManifest, root: _Reader) -> None:
    topic_ids = {topic.topic_id for topic in manifest.topics}
    card_ids = {card.topic_id for card in manifest.comparison_cards}
    for topic_id in sorted(topic_ids - card_ids):
        root.issues.append(
            Issue(CONFIG_REFERENCE, f"主题缺少对照卡：{topic_id}", root.source,
                  manifest.chapter_id, topic_id)
        )
    for topic_id in sorted(card_ids - topic_ids):
        root.issues.append(
            Issue(CONFIG_REFERENCE, f"对照卡引用未知主题：{topic_id}", root.source,
                  manifest.chapter_id, topic_id)
        )
    boundary_topic_ids = {boundary.topic_id for boundary in manifest.boundaries}
    for topic_id in sorted(topic_ids - boundary_topic_ids):
        root.issues.append(
            Issue(CONFIG_REFERENCE, f"主题缺少边界记录：{topic_id}", root.source,
                  manifest.chapter_id, topic_id)
        )
    for topic_id in sorted(boundary_topic_ids - topic_ids):
        root.issues.append(
            Issue(CONFIG_REFERENCE, f"边界记录引用未知主题：{topic_id}", root.source,
                  manifest.chapter_id, topic_id)
        )


def _validate_exercise_links(manifest: ChapterManifest, root: _Reader) -> None:
    exercise_by_id = {exercise.exercise_id: exercise for exercise in manifest.exercises}
    acceptance_by_id = {
        acceptance.acceptance_id: acceptance for acceptance in manifest.acceptances
    }
    exercise_pattern = re.compile(r"^CH\d{2}-EX\d{2}$")
    for exercise in manifest.exercises:
        if not exercise_pattern.fullmatch(exercise.exercise_id):
            root.issues.append(
                Issue(CONFIG_VALUE, f"练习标识格式无效：{exercise.exercise_id}", root.source,
                      manifest.chapter_id, exercise.exercise_id)
            )
        acceptance = acceptance_by_id.get(exercise.acceptance_id)
        if acceptance is None:
            message = f"练习引用未知验收：{exercise.acceptance_id}"
        elif acceptance.exercise_id != exercise.exercise_id:
            message = f"练习与验收反向引用不一致：{exercise.exercise_id}"
        else:
            continue
        root.issues.append(
            Issue(CONFIG_REFERENCE, message, root.source,
                  manifest.chapter_id, exercise.exercise_id)
        )
    for acceptance in manifest.acceptances:
        linked_exercise = exercise_by_id.get(acceptance.exercise_id)
        if linked_exercise is None:
            message = f"验收引用未知练习：{acceptance.exercise_id}"
        elif linked_exercise.acceptance_id != acceptance.acceptance_id:
            message = f"验收与练习反向引用不一致：{acceptance.acceptance_id}"
        else:
            continue
        root.issues.append(
            Issue(CONFIG_REFERENCE, message, root.source,
                  manifest.chapter_id, acceptance.acceptance_id)
        )


def _validate_trace_links(manifest: ChapterManifest, root: _Reader) -> None:
    artifact_ids = {manifest.chapter_id}
    artifact_ids.update(topic.topic_id for topic in manifest.topics)
    artifact_ids.update(example.example_id for example in manifest.examples)
    artifact_ids.update(boundary.boundary_id for boundary in manifest.boundaries)
    artifact_ids.update(exercise.exercise_id for exercise in manifest.exercises)
    artifact_ids.update(acceptance.acceptance_id for acceptance in manifest.acceptances)
    for link in manifest.trace_links:
        if link.artifact_id not in artifact_ids:
            root.issues.append(
                Issue(CONFIG_REFERENCE, f"追踪工件不存在：{link.artifact_id}", root.source,
                      manifest.chapter_id, link.artifact_id)
            )


def load_chapter_manifest(
    path: Path, repo_root: Path | None = None
) -> ChapterManifest:
    result = try_load_chapter_manifest(path, repo_root)
    if result.value is None:
        raise ContentModelError(result.issues)
    return result.value
