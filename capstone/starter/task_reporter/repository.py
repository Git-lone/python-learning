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
        raise TaskDataError(f"cannot read task data: {path}") from error

    if not isinstance(raw, list):
        raise TaskDataError("task data root must be an array")
    try:
        return [Task.from_mapping(item, index) for index, item in enumerate(raw)]
    except ValueError as error:
        raise TaskDataError(str(error)) from error
