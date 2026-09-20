"""任务报告器命令行入口。"""

import argparse
from collections.abc import Sequence
from pathlib import Path

from .repository import TaskDataError, load_tasks
from .report import render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成任务完成情况报告")
    # type=Path 只转换参数类型，不证明文件存在；读取和错误处理交给 repository。
    parser.add_argument("--input", type=Path, required=True, help="UTF-8 JSON 任务文件")
    parser.add_argument("--owner", help="只保留指定负责人，区分大小写")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    # argv=None 读取真实命令行；测试传字符串列表即可，无需修改全局 sys.argv。
    arguments = build_parser().parse_args(argv)
    try:
        tasks = load_tasks(arguments.input)
    except TaskDataError as error:
        # 在最外层把领域错误转成面向用户的信息与非零退出码，内部函数不直接退出进程。
        print(f"ERROR: {error}")
        return 2
    if arguments.owner is not None:
        # 先过滤再聚合，报告中的总数和完成率都基于筛选后的任务集合。
        tasks = [task for task in tasks if task.owner == arguments.owner]
    print(render_report(tasks))
    return 0
