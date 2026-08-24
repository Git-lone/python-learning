"""练习：用 Semaphore 限制协程并发量。"""

from collections.abc import Awaitable, Iterable
from typing import TypeVar

T = TypeVar("T")


async def run_limited(tasks: Iterable[Awaitable[T]], limit: int) -> list[T]:
    """并发等待任务并保持输入顺序；limit 必须大于 0。"""
    raise NotImplementedError("请完成 CH10-EX01")
