from __future__ import annotations

# Feature: python-learning-for-java-developers, Property 1: 课程目录同构
# **Validates: Requirements 1.2, 1.3, 1.4, 1.10, 16.14, 16.15, 16.16**

from pathlib import Path
import re

from hypothesis import given, settings, strategies as st

from tools.content_model import load_catalog


ROOT = Path(__file__).resolve().parents[2]
CHAPTERS = ROOT / "learning/chapters"
CATALOG = load_catalog(ROOT / "learning/catalog.toml", ROOT)
CourseEntry = tuple[int, str, Path]


def _directory_entries() -> tuple[CourseEntry, ...]:
    entries: list[CourseEntry] = []
    for directory in sorted(CHAPTERS.iterdir()):
        match = re.fullmatch(r"(\d{2})-.+", directory.name)
        if not directory.is_dir() or match is None:
            continue
        entry = directory / "README.md"
        heading = entry.read_text(encoding="utf-8").splitlines()[0]
        title_match = re.fullmatch(r"# 第 (\d+) 章：(.+)", heading)
        assert title_match is not None, f"章节标题格式错误：{entry}"
        number = int(match.group(1))
        assert number == int(title_match.group(1)), f"目录编号与标题编号不一致：{entry}"
        entries.append((number, title_match.group(2), entry.resolve().relative_to(ROOT)))
    return tuple(entries)


def _catalog_entries() -> tuple[CourseEntry, ...]:
    return tuple((chapter.number, chapter.title, chapter.entry) for chapter in CATALOG.chapters)


def _document_entries(path: Path) -> tuple[CourseEntry, ...]:
    entries: list[CourseEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\|\s*\d+\s*\|", line) is None:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        target = re.search(r"\]\(([^)#]+)(?:#[^)]+)?\)", cells[3])
        assert target is not None, f"导航条目缺少入口链接：{path}：{line}"
        entry = (path.parent / target.group(1)).resolve().relative_to(ROOT)
        entries.append((int(cells[0]), cells[1], entry))
    return tuple(entries)


def _course_views() -> dict[str, tuple[CourseEntry, ...]]:
    return {
        "实际章节目录": _directory_entries(),
        "catalog": _catalog_entries(),
        "根 README": _document_entries(ROOT / "README.md"),
        "INDEX": _document_entries(ROOT / "learning/INDEX.md"),
    }


@given(indices=st.lists(st.integers(min_value=0, max_value=len(CATALOG.chapters) - 1), max_size=32))
@settings(max_examples=100, deadline=None)
def test_course_catalog_views_are_isomorphic(indices: list[int]) -> None:
    views = _course_views()
    expected = views["catalog"]
    expected_numbers = tuple(range(1, len(expected) + 1))

    assert expected, "课程目录不得为空"
    for name, entries in views.items():
        assert len(entries) == len(expected), f"{name} 的章节数量与 catalog 不一致"
        assert tuple(item[0] for item in entries) == expected_numbers, f"{name} 的编号不连续"
        assert len(set(entries)) == len(entries), f"{name} 存在重复章节条目"
        assert len({item[2] for item in entries}) == len(entries), f"{name} 存在重复入口"
        assert set(entries) == set(expected), f"{name} 与 catalog 未形成双射"
        assert entries == expected, f"{name} 的编号、主题、顺序或入口与 catalog 不一致"
        assert all((ROOT / item[2]).is_file() for item in entries), f"{name} 包含不存在的入口"

    expected_projection = tuple(expected[index] for index in indices)
    for name, entries in views.items():
        assert tuple(entries[index] for index in indices) == expected_projection, (
            f"{name} 在受控章节投影下与 catalog 不一致"
        )
