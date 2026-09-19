"""CH10-EX01 参考答案。"""

import asyncio
from collections.abc import Awaitable, Iterable
from typing import TypeVar

T = TypeVar("T")


async def run_limited(tasks: Iterable[Awaitable[T]], limit: int) -> list[T]:
    if limit < 1:
        raise ValueError("limit must be positive")
    semaphore = asyncio.Semaphore(limit)

    async def run_one(task: Awaitable[T]) -> T:
        async with semaphore:
            return await task

    async with asyncio.TaskGroup() as group:
        scheduled = [group.create_task(run_one(task)) for task in tasks]
    return [task.result() for task in scheduled]
