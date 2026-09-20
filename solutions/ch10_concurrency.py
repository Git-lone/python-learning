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
        # 上下文退出时释放许可，包括异常路径；不要手工 acquire 后漏掉 release。
        async with semaphore:
            return await task

    # 这里限制的是进入 await 的数量，不限制包装任务的创建数量。
    # 传入尚未运行的协程才能限制其执行；已调度的 Task 不会被此信号量暂停。
    async with asyncio.TaskGroup() as group:
        scheduled = [group.create_task(run_one(task)) for task in tasks]
    # TaskGroup 正常退出后再取结果，按输入顺序返回，而非按完成顺序返回。
    return [task.result() for task in scheduled]
