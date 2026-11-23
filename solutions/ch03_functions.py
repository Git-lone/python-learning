"""CH03-EX01 参考答案。"""

from collections.abc import Callable


def make_discount(rate: float) -> Callable[[float], float]:
    """校验折扣比例并返回计算函数；例如 0.2 表示减去原价的 20%。

    返回值类似捕获局部变量的 Java lambda，每次创建的函数保留各自的 rate。
    """

    # 在创建折扣函数时校验配置，不必等到真正计算某一笔价格才发现错误。
    if not 0 <= rate <= 1:
        raise ValueError("rate must be between 0 and 1")

    def apply_discount(price: float) -> float:
        """接受原价，返回按 round 规则保留两位小数的折后价。"""

        # 闭包保留本次调用的 rate；float/round 用于语法练习，精确金额可参考 CH04。
        return round(price * (1 - rate), 2)

    # 返回函数对象，不加括号；调用方稍后传入价格再执行它。
    return apply_discount
