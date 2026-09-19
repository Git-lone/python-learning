"""任务领域模型和外部数据校验。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Task:
    title: str
    owner: str
    estimate_minutes: int
    done: bool = False

    @classmethod
    def from_mapping(cls, data: object, index: int) -> Task:
        """把不可信 JSON 值转换为经过校验的 Task。"""
        if not isinstance(data, dict):
            raise ValueError(f"task[{index}] must be an object")

        title = data.get("title")
        owner = data.get("owner")
        estimate = data.get("estimate_minutes")
        done = data.get("done", False)
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"task[{index}].title must be a non-empty string")
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError(f"task[{index}].owner must be a non-empty string")
        if isinstance(estimate, bool) or not isinstance(estimate, int) or estimate < 0:
            raise ValueError(f"task[{index}].estimate_minutes must be a non-negative integer")
        if not isinstance(done, bool):
            raise ValueError(f"task[{index}].done must be a boolean")
        return cls(title.strip(), owner.strip(), estimate, done)
