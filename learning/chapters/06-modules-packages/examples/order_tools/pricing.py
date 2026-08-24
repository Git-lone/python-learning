"""订单价格计算实现。"""

from collections.abc import Iterable


def gross_total(amounts: Iterable[float], tax_rate: float = 0.2) -> float:
    return round(sum(amounts) * (1 + tax_rate), 2)
