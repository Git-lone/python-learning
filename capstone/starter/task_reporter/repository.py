"""从 JSON 文件读取任务。"""

import json
from pathlib import Path

from .model import Task


class TaskDataError(ValueError):
    """任务文件不可读或内容不符合契约。"""


def load_tasks(path: Path) -> list[Task]:
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
