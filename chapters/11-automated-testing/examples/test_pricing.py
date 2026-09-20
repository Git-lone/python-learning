"""pytest 参数化与异常断言示例。"""

from decimal import Decimal

import pytest

from sample.pricing import percentage_discount


# 一组数据生成一个独立测试，失败时可定位具体边界；字符串避免 float 精度干扰。
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
    # 不只断言抛异常，还用 match 检查错误原因，防止无关异常让用例误通过。
    with pytest.raises(ValueError, match="negative"):
        percentage_discount(Decimal("-1"), Decimal("0.1"))
