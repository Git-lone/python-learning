"""CH10-EX01 参考答案：用信号量限制协程同时进入工作的数量。

asyncio 在事件循环中协作调度，适合会主动让出执行权的异步 I/O；
这里没有创建 Java 线程池那样的工作线程，也不会让 CPU 计算自动并行。
"""

import asyncio
from collections.abc import Awaitable, Iterable
from typing import TypeVar

T = TypeVar("T")


async def run_limited(tasks: Iterable[Awaitable[T]], limit: int) -> list[T]:
    """运行一组可等待对象，并按输入顺序返回同类型的结果。

    limit 必须为正数。要限制实际工作的启动数量，应传入尚未调度的协程；
    信号量只能约束本函数管理的执行入口，无法约束已经运行的外部任务。
    """
    if limit < 1:
        raise ValueError("limit must be positive")
    semaphore = asyncio.Semaphore(limit)

    async def run_one(task: Awaitable[T]) -> T:
        """取得一个并发名额后等待工作完成，让返回值继续保持泛型 T。"""
        # 上下文退出时释放许可，包括异常路径；不要手工 acquire 后漏掉 release。
        async with semaphore:
            return await task

    # 这里限制的是进入 await 的数量，不限制包装任务的创建数量。
    # 传入尚未运行的协程才能限制其执行；已调度的 Task 不会被此信号量暂停。
    # TaskGroup 管理共同生命周期：子任务发生非取消异常时取消其余任务，
    # 等待清理后向外传播异常；普通子任务异常通常以 ExceptionGroup 汇总。
    async with asyncio.TaskGroup() as group:
        scheduled = [group.create_task(run_one(task)) for task in tasks]
    # TaskGroup 正常退出后再取结果，按输入顺序返回，而非按完成顺序返回。
    return [task.result() for task in scheduled]
