"""练习：为边界行为编写 pytest 测试。"""

from decimal import Decimal


def fixed_discount(price: Decimal, amount: Decimal) -> Decimal:
    """价格最低降到 0；这是练习中的被测函数。"""
    return max(Decimal("0"), price - amount)


def test_discount_never_becomes_negative() -> None:
    """补充 Arrange/Act/Assert，并验证折扣大于价格的边界。"""
    raise NotImplementedError("请完成 CH11-EX01")
