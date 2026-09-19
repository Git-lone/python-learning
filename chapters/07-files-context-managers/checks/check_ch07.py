"""CH07-EX01 自动验收。"""

from pathlib import Path

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_non_blank_lines_are_counted_without_loading_requirements(tmp_path: Path) -> None:
    source = tmp_path / "lines.txt"
    source.write_text("first\n\n  \nsecond\n", encoding="utf-8")
    assert target.count_non_blank_lines(source) == 2
    source.unlink()


def test_empty_file_has_zero_non_blank_lines(tmp_path: Path) -> None:
    source = tmp_path / "empty.txt"
    source.write_text("", encoding="utf-8")
    assert target.count_non_blank_lines(source) == 0


def test_missing_file_error_is_not_hidden(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        target.count_non_blank_lines(tmp_path / "missing.txt")
