"""折扣计算。"""

from decimal import Decimal


def percentage_discount(price: Decimal, rate: Decimal) -> Decimal:
    if price < 0:
        raise ValueError("price must not be negative")
    if not Decimal("0") <= rate <= Decimal("1"):
        raise ValueError("rate must be between 0 and 1")
    # quantize 将结果量化到分，按当前 Decimal 上下文舍入；默认是 ROUND_HALF_EVEN。
    return (price * (Decimal("1") - rate)).quantize(Decimal("0.01"))
