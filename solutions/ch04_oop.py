"""CH04-EX01 参考答案。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Money:
    """以 Decimal 和币种组成金额值对象，dataclass 自动生成初始化与比较方法。

    frozen 禁止给字段重新赋值，slots 限定实例字段；币种和金额精度由调用方约定。
    """

    amount: Decimal
    currency: str

    def __add__(self, other: Money) -> Money:
        """实现 money_a + money_b；返回同币种新值，币种不一致时抛出 ValueError。"""

        # 运算符重载只处理同币种相加，不能把不同币种的数值直接合并。
        if self.currency != other.currency:
            raise ValueError("cannot add different currencies")
        # 值对象返回新实例，原来的两个金额都不发生变化。
        return Money(self.amount + other.amount, self.currency)
