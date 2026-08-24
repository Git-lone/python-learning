"""基础语法：名称绑定、分支、循环和格式化输出。"""


def classify_score(score: int) -> str:
    """把分数转换为简单等级。"""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def main() -> int:
    customer = "Alice"
    unit_price = 20.0
    quantities = [1, 2]
    total = unit_price * sum(quantities)

    print(f"customer={customer} total={total:.2f}")
    print(f"grade={classify_score(82)} items={len(quantities)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
