"""pytest 参数化与异常断言示例。"""

from decimal import Decimal

import pytest

from sample.pricing import percentage_discount


@pytest.mark.parametrize(
    ("price", "rate", "expected"),
    [
        ("100", "0.20", "80.00"),
        ("19.99", "0", "19.99"),
    ],
)
def test_percentage_discount(price: str, rate: str, expected: str) -> None:
    assert percentage_discount(Decimal(price), Decimal(rate)) == Decimal(expected)


def test_negative_price_is_rejected() -> None:
    with pytest.raises(ValueError, match="negative"):
        percentage_discount(Decimal("-1"), Decimal("0.1"))
