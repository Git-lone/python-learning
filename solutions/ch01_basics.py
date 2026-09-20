"""CH01-EX01 参考答案。"""


def describe_order(unit_price: float, quantity: int) -> str:
    # 条件表达式先写结果再写条件；边界 quantity == 3 属于 bulk。
    size = "bulk" if quantity >= 3 else "normal"
    # .2f 控制输出格式，确保整数金额也显示小数部分。
    return f"quantity={quantity} total={unit_price * quantity:.2f} size={size}"
