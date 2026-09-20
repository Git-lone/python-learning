"""练习：实现惰性分块生成器。"""

from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")


def chunked(items: Iterable[T], size: int) -> Iterator[list[T]]:
    """按 size 惰性产出列表；size 小于 1 时抛出 ValueError。"""
    # 最后一批不足 size 也要保留；产出新批次后，之前交给调用方的列表不能跟着改变。
    raise NotImplementedError("请完成 CH09-EX01")
