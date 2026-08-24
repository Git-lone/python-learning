"""练习：实现不可变值对象。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __add__(self, other: Money) -> Money:
        """同币种相加；币种不同则抛出 ValueError。"""
        raise NotImplementedError("请完成 CH04-EX01")
