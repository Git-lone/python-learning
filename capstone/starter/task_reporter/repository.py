"""从 JSON 文件读取任务。"""

import json
from pathlib import Path

from .model import Task


class TaskDataError(ValueError):
    """任务文件不可读或内容不符合契约。"""


def load_tasks(path: Path) -> list[Task]:
    """一次读取 UTF-8 JSON 数组并转换为任务列表，不返回部分校验通过的结果。

    文件系统错误、JSON 语法错误及字段错误转换为 TaskDataError；
    UTF-8 解码失败产生的 UnicodeDecodeError 未被本例捕获，会直接向上传播。
    """

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        # 将文件和 JSON 语法错误转换为统一领域异常，同时保留原始异常链。
        raise TaskDataError(f"cannot read task data: {path}") from error

    if not isinstance(raw, list):
        raise TaskDataError("task data root must be an array")
    try:
        # 给每一项带上索引以定位坏数据；任何一项失败就整体报错，不静默跳过。
        return [Task.from_mapping(item, index) for index, item in enumerate(raw)]
    except ValueError as error:
        raise TaskDataError(str(error)) from error
