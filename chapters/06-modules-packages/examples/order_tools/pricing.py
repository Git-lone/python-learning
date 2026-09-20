"""订单价格计算实现。"""

from collections.abc import Iterable


def gross_total(amounts: Iterable[float], tax_rate: float = 0.2) -> float:
    # 接收 Iterable，因此列表和生成器都可使用；float 仅用于演示，金额精度见 CH08。
    return round(sum(amounts) * (1 + tax_rate), 2)
