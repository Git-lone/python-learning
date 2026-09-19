"""任务报告器命令行入口。"""

import argparse
from collections.abc import Sequence
from pathlib import Path

from .repository import TaskDataError, load_tasks
from .report import render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成任务完成情况报告")
    parser.add_argument("--input", type=Path, required=True, help="UTF-8 JSON 任务文件")
    parser.add_argument("--owner", help="只保留指定负责人，区分大小写")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        tasks = load_tasks(arguments.input)
    except TaskDataError as error:
        print(f"ERROR: {error}")
        return 2
    if arguments.owner is not None:
        tasks = [task for task in tasks if task.owner == arguments.owner]
    print(render_report(tasks))
    return 0
