"""CH01-EX01 参考答案。"""


def describe_order(unit_price: float, quantity: int) -> str:
    size = "bulk" if quantity >= 3 else "normal"
    return f"quantity={quantity} total={unit_price * quantity:.2f} size={size}"
