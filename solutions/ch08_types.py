"""CH08-EX01 参考答案。"""

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def first_or_none(items: Iterable[T]) -> T | None:
    """返回首项或 None；泛型 T 保留输入元素与返回值的类型关系。

    传入迭代器时会消耗它的一个元素，类型注解本身不会进行运行时校验。
    """

    # Iterable 不保证支持下标或 len；取到首项立即返回，也适用于一次性生成器。
    # 若首项本身为 None，返回值与空输入相同，这是当前接口的约定。
    for item in items:
        return item
    return None
