"""课程文档、目录、链接和需求追踪的一致性验证器。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from urllib.parse import unquote

from tools.content_model import (
    ChapterManifest,
    ChapterRef,
    CourseCatalog,
    Issue,
    sort_issues,
    try_load_catalog,
    try_load_chapter_manifest,
)

SECTIONS = (
    "学习目标",
    "Java 对照",
    "Python 知识",
    "可运行示例",
    "练习",
    "验证方式",
    "章节总结",
)

CATALOG_DIRECTORY_UNLISTED = "CATALOG-DIRECTORY-UNLISTED"
DOC_MANIFEST_MISSING = "DOC-MANIFEST-MISSING"
DOC_READ_FAILED = "DOC-READ-FAILED"
DOC_SECTION_MISSING = "DOC-SECTION-MISSING"
DOC_SECTION_DUPLICATE = "DOC-SECTION-DUPLICATE"
DOC_SECTION_ORDER = "DOC-SECTION-ORDER"
DOC_SECTION_EMPTY = "DOC-SECTION-EMPTY"
DOC_OBJECTIVE_COUNT = "DOC-OBJECTIVE-COUNT"
DOC_COMPARISON_MISSING = "DOC-COMPARISON-MISSING"
DOC_COMPARISON_DUPLICATE = "DOC-COMPARISON-DUPLICATE"
DOC_COMPARISON_FIELD_MISSING = "DOC-COMPARISON-FIELD-MISSING"
DOC_CODE_FENCE_LANGUAGE = "DOC-CODE-FENCE-LANGUAGE"
DOC_RUN_RECORD_MISSING = "DOC-RUN-RECORD-MISSING"
DOC_RUN_RECORD_DUPLICATE = "DOC-RUN-RECORD-DUPLICATE"
DOC_EXAMPLE_UNRECORDED = "DOC-EXAMPLE-UNRECORDED"
DOC_EXERCISE_COUNT = "DOC-EXERCISE-COUNT"
DOC_EXERCISE_UNLISTED = "DOC-EXERCISE-UNLISTED"
DOC_CHAPTER_ID_MISMATCH = "DOC-CHAPTER-ID-MISMATCH"
NAV_CATALOG_MISMATCH = "NAV-CATALOG-MISMATCH"
NAV_DOCUMENT_MISMATCH = "NAV-DOCUMENT-MISMATCH"
DOC_LINK_OUTSIDE_REPO = "DOC-LINK-OUTSIDE-REPO"
DOC_LINK_MISSING = "DOC-LINK-MISSING"
DOC_LINK_ANCHOR_MISSING = "DOC-LINK-ANCHOR-MISSING"
TRACE_REQUIREMENT_UNCOVERED = "TRACE-REQUIREMENT-UNCOVERED"
TRACE_REQUIREMENT_MISMATCH = "TRACE-REQUIREMENT-MISMATCH"

_SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_FENCE_PATTERN = re.compile(r"^```([^\s`]*)[^\n]*\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)
_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
_NAV_ROW_PATTERN = re.compile(r"^\|\s*(\d+)\s*\|", re.MULTILINE)
_COMPARISON_FIELDS = (
    "共同用途",
    "可验证行为差异",
    "Python 适用场景",
    "Java 开发者常见误区",
    "修正方式",
)


@dataclass(frozen=True)
class NavigationRow:
    number: int
    title: str
    entry: Path


def _issue(
    code: str,
    message: str,
    path: Path,
    chapter_id: str | None = None,
    entity_id: str | None = None,
) -> Issue:
    return Issue(code, message, path.resolve(), chapter_id, entity_id)


def _read_text(path: Path, chapter_id: str | None = None) -> tuple[str | None, list[Issue]]:
    try:
        return path.read_text(encoding="utf-8"), []
    except (OSError, UnicodeError) as error:
        return None, [_issue(DOC_READ_FAILED, f"无法读取 UTF-8 文档：{error}", path, chapter_id)]


def _section_spans(text: str) -> list[tuple[str, int, int]]:
    matches = list(_SECTION_PATTERN.finditer(text))
    return [
        (match.group(1).strip(), match.end(), matches[index + 1].start() if index + 1 < len(matches) else len(text))
        for index, match in enumerate(matches)
    ]


def validate_chapter_template(path: Path, chapter_id: str) -> list[Issue]:
    text, issues = _read_text(path, chapter_id)
    if text is None:
        return issues
    spans = _section_spans(text)
    names = [name for name, _, _ in spans]
    for section in SECTIONS:
        count = names.count(section)
        if count == 0:
            issues.append(_issue(DOC_SECTION_MISSING, f"缺少“{section}”部分", path, chapter_id, section))
        elif count > 1:
            issues.append(_issue(DOC_SECTION_DUPLICATE, f"“{section}”部分出现 {count} 次", path, chapter_id, section))
        for name, start, end in spans:
            if name == section and not _has_body(text[start:end]):
                issues.append(_issue(DOC_SECTION_EMPTY, f"“{section}”部分没有非空正文", path, chapter_id, section))
    found = [name for name in names if name in SECTIONS]
    expected_found = [name for name in SECTIONS if name in found]
    if found != expected_found:
        issues.append(_issue(DOC_SECTION_ORDER, "七个固定部分未按规定顺序排列", path, chapter_id))
    objective_span = next(((start, end) for name, start, end in spans if name == "学习目标"), None)
    if objective_span is not None:
        body = text[objective_span[0]:objective_span[1]]
        count = sum(bool(re.match(r"^\s*[-*]\s+\S", line)) for line in body.splitlines())
        if not 3 <= count <= 5:
            issues.append(_issue(DOC_OBJECTIVE_COUNT, f"学习目标数量必须为 3..5，实际为 {count}", path, chapter_id))
    issues.extend(_validate_code_fences(text, path, chapter_id))
    return issues


def _has_body(body: str) -> bool:
    return any(
        line.strip() and not line.lstrip().startswith(("#", "<!--"))
        for line in body.splitlines()
    )


def _validate_code_fences(text: str, path: Path, chapter_id: str) -> list[Issue]:
    issues: list[Issue] = []
    for index, match in enumerate(_FENCE_PATTERN.finditer(text), 1):
        language, code = match.group(1), match.group(2)
        expected: str | None = None
        if language in {"py", "python3", "Python", "PYTHON"}:
            expected = "python"
        elif language in {"Java", "JAVA"}:
            expected = "java"
        elif not language or language not in {"python", "java"}:
            if re.search(r"\b(public\s+class|System\.out\.|static\s+void\s+main)\b", code):
                expected = "java"
            elif re.search(r"(^|\n)\s*(def |from \S+ import |import \S+|if __name__)", code):
                expected = "python"
        if expected is not None and language != expected:
            shown = language or "未标记"
            issues.append(_issue(DOC_CODE_FENCE_LANGUAGE, f"第 {index} 个 {expected} 代码围栏标识为“{shown}”，应为“{expected}”", path, chapter_id, str(index)))
    return issues


def validate_manifest_document(
    manifest: ChapterManifest,
    chapter: ChapterRef,
    readme: Path,
    repo_root: Path,
) -> list[Issue]:
    text, issues = _read_text(readme, chapter.chapter_id)
    if text is None:
        return issues
    if manifest.chapter_id != chapter.chapter_id:
        issues.append(_issue(DOC_CHAPTER_ID_MISMATCH, f"章节清单标识为 {manifest.chapter_id}，目录条目为 {chapter.chapter_id}", readme, chapter.chapter_id))
    for topic in manifest.topics:
        count = len(re.findall(rf"\{{#{re.escape(topic.comparison_anchor)}\}}", text))
        if count == 0:
            issues.append(_issue(DOC_COMPARISON_MISSING, f"主题 {topic.topic_id} 缺少对照卡锚点 {topic.comparison_anchor}", readme, chapter.chapter_id, topic.topic_id))
        elif count > 1:
            issues.append(_issue(DOC_COMPARISON_DUPLICATE, f"主题 {topic.topic_id} 的对照卡出现 {count} 次", readme, chapter.chapter_id, topic.topic_id))
        else:
            anchor = text.index(f"{{#{topic.comparison_anchor}}}")
            end_candidates = [position for position in (text.find("\n### ", anchor + 1), text.find("\n## ", anchor + 1)) if position >= 0]
            card_text = text[anchor:min(end_candidates) if end_candidates else len(text)]
            for field in _COMPARISON_FIELDS:
                if not re.search(rf"^\s*[-*]\s*{re.escape(field)}\s*[：:]\s*\S", card_text, re.MULTILINE):
                    issues.append(_issue(DOC_COMPARISON_FIELD_MISSING, f"主题 {topic.topic_id} 的对照卡缺少非空“{field}”", readme, chapter.chapter_id, topic.topic_id))
    for example in manifest.examples:
        patterns = (
            rf"^###\s*(?:运行记录|示例)\s*[：:]\s*{re.escape(example.example_id)}\s*$",
            rf"\{{#run-{re.escape(example.example_id)}\}}",
        )
        count = sum(len(re.findall(pattern, text, re.MULTILINE)) for pattern in patterns)
        if count == 0:
            issues.append(_issue(DOC_RUN_RECORD_MISSING, f"示例 {example.example_id} 缺少文档运行记录", readme, chapter.chapter_id, example.example_id))
        elif count > 1:
            issues.append(_issue(DOC_RUN_RECORD_DUPLICATE, f"示例 {example.example_id} 有 {count} 份文档运行记录", readme, chapter.chapter_id, example.example_id))
    issues.extend(_validate_example_bijection(manifest, chapter, repo_root))
    issues.extend(_validate_exercises(manifest, chapter, repo_root))
    issues.extend(_validate_trace_coverage(manifest, readme))
    return issues


def _validate_example_bijection(
    manifest: ChapterManifest, chapter: ChapterRef, repo_root: Path
) -> list[Issue]:
    issues: list[Issue] = []
    example_dir = repo_root / chapter.directory / "examples"
    discovered: set[Path] = set()
    if example_dir.is_dir():
        for source in example_dir.rglob("*.py"):
            if source.name == "__init__.py":
                continue
            relative_to_examples = source.relative_to(example_dir)
            if len(relative_to_examples.parts) == 1:
                discovered.add(source.resolve().relative_to(repo_root.resolve()))
                continue
            try:
                content = source.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if "__name__" in content and "__main__" in content:
                discovered.add(source.resolve().relative_to(repo_root.resolve()))
    recorded = {example.source for example in manifest.examples}
    for source in sorted(discovered - recorded, key=lambda value: value.as_posix()):
        issues.append(_issue(DOC_EXAMPLE_UNRECORDED, f"可运行示例没有清单运行记录：{source.as_posix()}", repo_root / source, chapter.chapter_id, source.as_posix()))
    return issues


def _validate_exercises(
    manifest: ChapterManifest, chapter: ChapterRef, repo_root: Path
) -> list[Issue]:
    issues: list[Issue] = []
    count = len(manifest.exercises)
    manifest_path = repo_root / chapter.directory / "chapter.toml"
    if not 1 <= count <= 3:
        issues.append(_issue(DOC_EXERCISE_COUNT, f"练习数量必须为 1..3，实际为 {count}", manifest_path, chapter.chapter_id))
    exercise_dir = repo_root / chapter.directory / "exercises"
    discovered = {
        path.resolve().relative_to(repo_root.resolve())
        for path in exercise_dir.rglob("exercise_*.py")
    } if exercise_dir.is_dir() else set()
    listed = {exercise.entry for exercise in manifest.exercises}
    for entry in sorted(discovered - listed, key=lambda value: value.as_posix()):
        issues.append(_issue(DOC_EXERCISE_UNLISTED, f"练习入口未列入章节清单：{entry.as_posix()}", repo_root / entry, chapter.chapter_id, entry.as_posix()))
    return issues


def _validate_trace_coverage(manifest: ChapterManifest, path: Path) -> list[Issue]:
    issues: list[Issue] = []
    links_by_requirement: dict[str, list[str]] = {}
    for link in manifest.trace_links:
        links_by_requirement.setdefault(link.requirement_id, []).append(link.artifact_id)
    for requirement_id in sorted(set(manifest.requirements) - links_by_requirement.keys()):
        issues.append(_issue(TRACE_REQUIREMENT_UNCOVERED, f"需求 {requirement_id} 没有需求到工件追踪链接", path, manifest.chapter_id, requirement_id))
    declared: dict[str, set[str]] = {manifest.chapter_id: set(manifest.requirements)}
    declared.update((topic.topic_id, set(topic.requirements)) for topic in manifest.topics)
    declared.update((example.example_id, set(example.requirements)) for example in manifest.examples)
    declared.update((boundary.boundary_id, set(boundary.requirements)) for boundary in manifest.boundaries)
    for link in manifest.trace_links:
        artifact_requirements = declared.get(link.artifact_id)
        if artifact_requirements is not None and link.requirement_id not in artifact_requirements:
            issues.append(_issue(TRACE_REQUIREMENT_MISMATCH, f"工件 {link.artifact_id} 未声明需求 {link.requirement_id}", path, manifest.chapter_id, link.artifact_id))
    return issues


def _navigation_rows(path: Path, repo_root: Path) -> tuple[list[NavigationRow], list[Issue]]:
    text, issues = _read_text(path)
    if text is None:
        return [], issues
    rows: list[NavigationRow] = []
    for line in text.splitlines():
        if _NAV_ROW_PATTERN.match(line) is None:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        target = re.search(r"\]\(([^)]+)\)", cells[3])
        if target is None:
            continue
        entry = (path.parent / unquote(target.group(1).split("#", 1)[0])).resolve()
        try:
            relative = entry.relative_to(repo_root.resolve())
        except ValueError:
            relative = entry
        rows.append(NavigationRow(int(cells[0]), cells[1], relative))
    return rows, issues


def validate_navigation(
    catalog: CourseCatalog, readme: Path, index: Path, repo_root: Path
) -> list[Issue]:
    issues: list[Issue] = []
    expected = [NavigationRow(item.number, item.title, item.entry) for item in catalog.chapters]
    readme_rows, readme_issues = _navigation_rows(readme, repo_root)
    index_rows, index_issues = _navigation_rows(index, repo_root)
    issues.extend(readme_issues)
    issues.extend(index_issues)
    for path, actual in ((readme, readme_rows), (index, index_rows)):
        if actual != expected:
            issues.append(_issue(NAV_CATALOG_MISMATCH, f"导航条目与课程清单不一致：期望 {len(expected)} 条，实际 {len(actual)} 条", path))
    if readme_rows != index_rows:
        issues.append(_issue(NAV_DOCUMENT_MISMATCH, "README 与 INDEX 的数量、编号、主题、顺序或入口不一致", index))
    return issues


def validate_links(documents: set[Path], repo_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    root = repo_root.resolve()
    for document in sorted(documents, key=lambda value: value.as_posix()):
        text, read_issues = _read_text(document)
        issues.extend(read_issues)
        if text is None:
            continue
        for raw_target in _LINK_PATTERN.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            file_part, separator, fragment = target.partition("#")
            resolved = (document.parent / unquote(file_part)).resolve() if file_part else document.resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                issues.append(_issue(DOC_LINK_OUTSIDE_REPO, f"链接指向仓库外：{raw_target}", document, entity_id=raw_target))
                continue
            if not resolved.is_file():
                issues.append(_issue(DOC_LINK_MISSING, f"链接目标不存在：{raw_target}", document, entity_id=raw_target))
                continue
            if separator and fragment and not _has_anchor(resolved, unquote(fragment)):
                issues.append(_issue(DOC_LINK_ANCHOR_MISSING, f"链接锚点不存在：{raw_target}", document, entity_id=raw_target))
    return issues


def _has_anchor(path: Path, fragment: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    if f"{{#{fragment}}}" in text:
        return True
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*$", text, re.MULTILINE):
        clean = re.sub(r"\s*\{#[^}]+\}\s*$", "", heading)
        slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", clean.lower()).strip("-")
        if slug == fragment:
            return True
    return False


def validate_repository(repo_root: Path) -> tuple[Issue, ...]:
    root = repo_root.resolve()
    catalog_result = try_load_catalog(root / "learning/catalog.toml", root)
    issues = list(catalog_result.issues)
    if catalog_result.value is None:
        return sort_issues(issues)
    catalog = catalog_result.value
    expected_directories = {(root / chapter.directory).resolve() for chapter in catalog.chapters}
    chapters_root = root / "learning/chapters"
    actual_directories = {
        path.resolve()
        for path in chapters_root.iterdir()
        if path.is_dir() and not path.name.startswith((".", "__"))
    } if chapters_root.is_dir() else set()
    for directory in sorted(actual_directories - expected_directories, key=lambda value: value.as_posix()):
        issues.append(_issue(CATALOG_DIRECTORY_UNLISTED, f"章节目录未列入课程清单：{directory.name}", directory, entity_id=directory.name))
    documents = {root / "README.md", root / "learning/INDEX.md"}
    for chapter in catalog.chapters:
        readme = root / chapter.entry
        documents.add(readme)
        issues.extend(validate_chapter_template(readme, chapter.chapter_id))
        manifest_path = root / chapter.directory / "chapter.toml"
        if not manifest_path.is_file():
            issues.append(_issue(DOC_MANIFEST_MISSING, "章节缺少 chapter.toml 清单（当前内容仍为占位）", manifest_path, chapter.chapter_id))
            continue
        manifest_result = try_load_chapter_manifest(manifest_path, root)
        issues.extend(manifest_result.issues)
        if manifest_result.value is not None:
            issues.extend(validate_manifest_document(manifest_result.value, chapter, readme, root))
        chapter_dir = root / chapter.directory
        if chapter_dir.is_dir():
            documents.update(chapter_dir.rglob("*.md"))
    issues.extend(validate_navigation(catalog, root / "README.md", root / "learning/INDEX.md", root))
    issues.extend(validate_links(documents, root))
    return sort_issues(issues)


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def format_issue(issue: Issue, repo_root: Path) -> str:
    chapter = issue.chapter_id or "COURSE"
    entity = f" | {issue.entity_id}" if issue.entity_id else ""
    return f"{issue.code} | {chapter} | {_display_path(issue.path, repo_root)}{entity} | {issue.message}"


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="校验课程内容、导航、链接和需求追踪")
    parser.add_argument("--root", type=Path, help="仓库根目录；默认自动取 tools 的父目录")
    args = parser.parse_args(argv)
    root = (repo_root or args.root or Path(__file__).resolve().parents[1]).resolve()
    issues = validate_repository(root)
    if issues:
        for issue in issues:
            print(format_issue(issue, root))
        print(f"内容校验失败：共 {len(issues)} 个问题", file=sys.stderr)
        return 1
    print("内容校验通过：未发现问题")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
