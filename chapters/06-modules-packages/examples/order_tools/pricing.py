"""订单价格计算实现。"""

from collections.abc import Iterable


def gross_total(amounts: Iterable[float], tax_rate: float = 0.2) -> float:
    """消费一遍金额序列并返回含税合计，税率 0.2 表示 20%。

    若传入生成器，本次求和会消耗它；本例不做金额、税率的业务范围校验。
    """

    # 接收 Iterable，因此列表和生成器都可使用；float 仅用于演示，金额精度见 CH08。
    return round(sum(amounts) * (1 + tax_rate), 2)
