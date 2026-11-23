"""TaskGroup、协程和把阻塞工作移出事件循环。"""

import asyncio


def blocking_label(label: str) -> str:
    """同步调用的占位函数；本例本身没有耗时 I/O，只用它演示线程适配。"""
    return f"sync-{label}"


async def async_label(label: str) -> str:
    """用非阻塞等待模拟异步 I/O；调用得到协程，调度或 await 后才执行。"""
    # await 等待期间让出事件循环；直接调用同步 sleep 会阻塞其他协程。
    await asyncio.sleep(0.01)
    return f"async-{label}"


async def collect() -> list[str]:
    """在同一任务组内运行同步适配与异步调用，全部成功后按固定顺序取结果。

    TaskGroup 负责等待和异常传播；与任意后台线程不同，子任务生命周期受作用域管理。
    取消等待线程结果的协程，并不保证已开始运行的同步函数会被强行中止。
    """

    # 正常离开 TaskGroup 时任务都已结束；任务异常时会取消同组未完成任务。
    async with asyncio.TaskGroup() as group:
        # 将同步调用放到线程。真实场景适合阻塞 I/O，不等于让纯 Python CPU 计算加速。
        sync_task = group.create_task(asyncio.to_thread(blocking_label, "A"))
        async_task = group.create_task(async_label("B"))
    # 按这里写定的顺序读取，不依赖两个任务完成的先后顺序。
    return [sync_task.result(), async_task.result()]


def main() -> int:
    print(f"results={asyncio.run(collect())}")
    print("event_loop=closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
