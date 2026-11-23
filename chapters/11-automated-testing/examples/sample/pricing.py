"""折扣计算。"""

from decimal import Decimal


def percentage_discount(price: Decimal, rate: Decimal) -> Decimal:
    """返回折后金额；rate 是减免比例，0.2 表示减 20%，不是支付 20%。

    拒绝负价格及区间 [0, 1] 外的折扣，方便测试正常结果和失败契约。
    """

    if price < 0:
        raise ValueError("price must not be negative")
    if not Decimal("0") <= rate <= Decimal("1"):
        raise ValueError("rate must be between 0 and 1")
    # quantize 将结果量化到分，按当前 Decimal 上下文舍入；默认是 ROUND_HALF_EVEN。
    return (price * (Decimal("1") - rate)).quantize(Decimal("0.01"))
