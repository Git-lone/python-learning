"""CH02-EX01 参考答案。"""

from collections.abc import Iterable


def even_squares(numbers: Iterable[int]) -> dict[int, int]:
    # 接收可迭代对象而非仅列表；重复偶数会落到同一个键，不会产生重复条目。
    return {number: number**2 for number in numbers if number % 2 == 0}
