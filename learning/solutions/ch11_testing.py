"""CH11-EX01 参考答案。"""

from decimal import Decimal


def fixed_discount(price: Decimal, amount: Decimal) -> Decimal:
    return max(Decimal("0"), price - amount)


def test_discount_never_becomes_negative() -> None:
    price = Decimal("5")
    amount = Decimal("8")

    actual = fixed_discount(price, amount)

    assert actual == Decimal("0")
