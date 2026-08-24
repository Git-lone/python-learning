"""CH08-EX01 参考答案。"""

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def first_or_none(items: Iterable[T]) -> T | None:
    for item in items:
        return item
    return None
