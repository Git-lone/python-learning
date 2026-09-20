"""练习：实现保留元素类型的泛型函数。"""

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def first_or_none(items: Iterable[T]) -> T | None:
    """返回第一个元素；空输入返回 None。"""
    # 支持列表和生成器，只消费必要的元素；返回值类型要保留输入元素的 T。
    raise NotImplementedError("请完成 CH08-EX01")
