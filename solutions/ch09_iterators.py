"""CH09-EX01 参考答案。"""

from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")


def chunked(items: Iterable[T], size: int) -> Iterator[list[T]]:
    # 函数含 yield，因此首次迭代才开始执行，size 校验也在那时发生。
    if size < 1:
        raise ValueError("size must be positive")
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            # 换一个新列表，不能 clear 已产出的列表，否则消费者保存的批次也会被清空。
            batch = []
    # 最后一批不足 size 仍需产出；空输入则不产生批次。
    if batch:
        yield batch
