"""CH02-EX01 参考答案。"""

from collections.abc import Iterable


def even_squares(numbers: Iterable[int]) -> dict[int, int]:
    return {number: number**2 for number in numbers if number % 2 == 0}
