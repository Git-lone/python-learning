"""练习：用 Semaphore 限制协程并发量。"""

from collections.abc import Awaitable, Iterable
from typing import TypeVar

T = TypeVar("T")


async def run_limited(tasks: Iterable[Awaitable[T]], limit: int) -> list[T]:
    """并发等待任务并保持输入顺序；limit 必须大于 0。"""
    # 验证并发上限与结果顺序两个条件；控制并发时请用尚未调度的协程作为输入。
    raise NotImplementedError("请完成 CH10-EX01")
