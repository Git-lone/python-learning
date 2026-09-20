"""CH11-EX01 参考答案。"""

from decimal import Decimal


def fixed_discount(price: Decimal, amount: Decimal) -> Decimal:
    return max(Decimal("0"), price - amount)


def test_discount_never_becomes_negative() -> None:
    # Arrange：特意选择折扣大于价格，覆盖普通折扣用例无法证明的下限行为。
    price = Decimal("5")
    amount = Decimal("8")

    # Act：只调用被测行为，不在测试中重新实现折扣算法。
    actual = fixed_discount(price, amount)

    # Assert：验证精确边界值，而不只是结果非负。
    assert actual == Decimal("0")
