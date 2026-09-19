"""练习：实现保留元素类型的泛型函数。"""

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def first_or_none(items: Iterable[T]) -> T | None:
    """返回第一个元素；空输入返回 None。"""
    raise NotImplementedError("请完成 CH08-EX01")
