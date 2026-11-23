"""任务领域模型和外部数据校验。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Task:
    """报告使用的任务值对象；外部 JSON 应通过 from_mapping 校验后构造。

    dataclass 本身不会校验字段，直接调用 Task(...) 会绕过下面的输入检查。
    """

    title: str
    owner: str
    estimate_minutes: int
    done: bool = False

    @classmethod
    def from_mapping(cls, data: object, index: int) -> Task:
        """校验单条 JSON 对象并清洗文本；index 用于错误定位，非法字段抛 ValueError。"""
        # JSON 解码可能得到列表、数字或 null；类型注解不会代替这些运行时检查。
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
        # Python 的 bool 继承 int，必须显式排除，避免 true 被当作一分钟。
        if isinstance(estimate, bool) or not isinstance(estimate, int) or estimate < 0:
            raise ValueError(f"task[{index}].estimate_minutes must be a non-negative integer")
        if not isinstance(done, bool):
            raise ValueError(f"task[{index}].done must be a boolean")
        # classmethod 通过 cls 构造实例；返回前统一去空白，下游报告无需重复清洗。
        return cls(title.strip(), owner.strip(), estimate, done)
