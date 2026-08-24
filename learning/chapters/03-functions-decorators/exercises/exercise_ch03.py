"""练习：编写带参数校验的闭包。"""

from collections.abc import Callable


def make_discount(rate: float) -> Callable[[float], float]:
    """创建折扣函数；rate 必须位于 0..1，结果保留两位小数。"""
    raise NotImplementedError("请完成 CH03-EX01")
