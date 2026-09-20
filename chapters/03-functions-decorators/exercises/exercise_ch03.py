"""练习：编写带参数校验的闭包。"""

from collections.abc import Callable


def make_discount(rate: float) -> Callable[[float], float]:
    """创建折扣函数；rate 必须位于 0..1，结果保留两位小数。"""
    # 返回的是接收价格的函数，不是计算结果；非法 rate 应在创建函数时抛出 ValueError。
    raise NotImplementedError("请完成 CH03-EX01")
