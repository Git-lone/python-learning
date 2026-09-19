"""Resolve manifest paths independently of the calling shell directory."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def catalog() -> list[dict[str, Any]]:
    with (ROOT / "catalog.toml").open("rb") as file:
        return list(tomllib.load(file)["chapters"])


def selected(parser: argparse.ArgumentParser) -> list[dict[str, Any]]:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--chapter", type=int)
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()
    chapters = catalog()
    if args.all:
        return chapters
    matches = [chapter for chapter in chapters if chapter["number"] == args.chapter]
    if not matches:
        parser.error(f"unknown chapter: {args.chapter}")
    return matches


def manifest(chapter: dict[str, Any]) -> dict[str, Any]:
    with (ROOT / chapter["directory"] / "chapter.toml").open("rb") as file:
        return dict(tomllib.load(file))


def run(
    command: list[str], *, timeout: int, cwd: Path = ROOT, target: Path | None = None
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT)
    env.pop("PYTHON_TUTORIAL_TARGET", None)
    if target is not None:
        env["PYTHON_TUTORIAL_TARGET"] = str(target)
    argv = [
        sys.executable if part == "python" and i == 0 else part for i, part in enumerate(command)
    ]
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=timeout,
        check=False,
    )
