"""CH03-EX01 参考答案。"""

from collections.abc import Callable


def make_discount(rate: float) -> Callable[[float], float]:
    if not 0 <= rate <= 1:
        raise ValueError("rate must be between 0 and 1")

    def apply_discount(price: float) -> float:
        return round(price * (1 - rate), 2)

    return apply_discount
