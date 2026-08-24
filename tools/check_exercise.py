"""运行章节练习验收测试，或验证参考答案。"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import os
from pathlib import Path
import subprocess
import sys

from tools.content_model import ChapterRef, load_catalog, load_chapter_manifest

TARGET_ENV = "PYTHON_TUTORIAL_TARGET"


def _matches(selector: str, chapter: ChapterRef) -> bool:
    normalized = selector.strip().lower()
    return normalized in {
        str(chapter.number),
        f"{chapter.number:02d}",
        chapter.chapter_id.lower(),
    }


def _solution_path(root: Path, chapter: ChapterRef) -> Path:
    matches = sorted((root / "learning" / "solutions").glob(f"ch{chapter.number:02d}_*.py"))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"{chapter.chapter_id} 需要且只能有一个参考答案，实际找到 {len(matches)} 个"
        )
    return matches[0]


def _run_check(root: Path, chapter: ChapterRef, *, solution: bool) -> int:
    manifest = load_chapter_manifest(root / chapter.directory / "chapter.toml", root)
    if not manifest.exercises:
        print(f"FAIL | {chapter.chapter_id} | 没有练习", file=sys.stderr)
        return 1
    target = _solution_path(root, chapter) if solution else root / manifest.exercises[0].entry
    check = root / chapter.directory / "checks" / f"check_ch{chapter.number:02d}.py"
    if not target.is_file() or not check.is_file():
        print(
            f"FAIL | {chapter.chapter_id} | 目标或检查文件不存在：{target} | {check}",
            file=sys.stderr,
        )
        return 1

    mode = "solution" if solution else "exercise"
    print(f"CHECK | {chapter.chapter_id} | {mode}")
    environment = os.environ.copy()
    environment[TARGET_ENV] = str(target.resolve())
    environment["PYTHONUTF8"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(check), "-q"],
        cwd=root,
        env=environment,
        check=False,
    )
    return completed.returncode


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 Python 教程练习验收")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--chapter", help="章节编号或 CHxx 标识")
    selection.add_argument("--all", action="store_true", help="运行全部章节练习")
    parser.add_argument("--solution", action="store_true", help="验证参考答案而非练习文件")
    return parser


def main(argv: Sequence[str] | None = None, *, repo_root: Path | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    catalog = load_catalog(root / "learning" / "catalog.toml", root)
    chapters = list(catalog.chapters)
    if arguments.chapter is not None:
        chapters = [chapter for chapter in chapters if _matches(arguments.chapter, chapter)]
        if not chapters:
            print(f"找不到章节：{arguments.chapter}", file=sys.stderr)
            return 2

    failures = sum(
        _run_check(root, chapter, solution=arguments.solution) != 0
        for chapter in chapters
    )
    if failures:
        print(f"FAIL | {failures} 个章节练习未通过", file=sys.stderr)
        return 1
    print(f"OK | 已通过 {len(chapters)} 个章节练习")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
