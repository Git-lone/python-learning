"""CH04-EX01 参考答案。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __add__(self, other: Money) -> Money:
        # 运算符重载只处理同币种相加，不能把不同币种的数值直接合并。
        if self.currency != other.currency:
            raise ValueError("cannot add different currencies")
        # 值对象返回新实例，原来的两个金额都不发生变化。
        return Money(self.amount + other.amount, self.currency)
