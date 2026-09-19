"""TaskGroup、协程和把阻塞工作移出事件循环。"""

import asyncio


def blocking_label(label: str) -> str:
    return f"sync-{label}"


async def async_label(label: str) -> str:
    await asyncio.sleep(0.01)
    return f"async-{label}"


async def collect() -> list[str]:
    async with asyncio.TaskGroup() as group:
        sync_task = group.create_task(asyncio.to_thread(blocking_label, "A"))
        async_task = group.create_task(async_label("B"))
    return [sync_task.result(), async_task.result()]


def main() -> int:
    print(f"results={asyncio.run(collect())}")
    print("event_loop=closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
