from __future__ import annotations

from pathlib import Path
import re

from tools.content_model import load_catalog


ROOT = Path(__file__).resolve().parents[2]
CATALOG = load_catalog(ROOT / "catalog.toml", ROOT)


def _rows(path: Path) -> list[tuple[int, str, str, Path]]:
    rows: list[tuple[int, str, str, Path]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| \d+ \|", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        target = re.search(r"\]\(([^)]+)\)", cells[3])
        assert target is not None
        rows.append((int(cells[0]), cells[1], cells[2], (path.parent / target.group(1)).resolve()))
    return rows


def test_catalog_has_continuous_unique_chapters_and_resolvable_entries() -> None:
    assert [chapter.number for chapter in CATALOG.chapters] == list(range(1, 25))
    assert len({chapter.chapter_id for chapter in CATALOG.chapters}) == 24
    assert len({chapter.entry for chapter in CATALOG.chapters}) == 24
    for chapter in CATALOG.chapters:
        assert all(prerequisite < chapter.number for prerequisite in chapter.prerequisites)
        text = (ROOT / chapter.entry).read_text(encoding="utf-8")
        assert any(line.strip() and not line.startswith("#") for line in text.splitlines())


def test_overview_and_index_match_catalog_and_prerequisites() -> None:
    expected = [(chapter.number, chapter.title, (ROOT / chapter.entry).resolve()) for chapter in CATALOG.chapters]
    for document in (ROOT / "README.md", ROOT / "INDEX.md"):
        rows = _rows(document)
        assert [(number, title, entry) for number, title, _, entry in rows] == expected
        for chapter, (_, _, shown, _) in zip(CATALOG.chapters, rows, strict=True):
            if not chapter.prerequisites:
                assert shown == "无"
            else:
                targets = [(document.parent / target).resolve() for target in re.findall(r"\]\(([^)]+)\)", shown)]
                assert targets == [(ROOT / CATALOG.chapters[number - 1].entry).resolve() for number in chapter.prerequisites]


def test_all_document_links_resolve() -> None:
    documents = [ROOT / "README.md", ROOT / "INDEX.md", *(ROOT / chapter.entry for chapter in CATALOG.chapters)]
    for document in documents:
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#")):
                continue
            assert (document.parent / target).resolve().is_file(), f"链接不存在：{document} -> {target}"
