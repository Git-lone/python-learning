"""基础语法：名称绑定、分支、循环和格式化输出。"""


def classify_score(score: int) -> str:
    """按从高到低的阈值返回等级；本例暂不校验分数是否位于 0～100。"""
    # return 会结束本次调用，所以先判断高分，避免高分提前落入低等级。
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def main() -> int:
    # Python 名称绑定到对象，无需像 Java 局部变量那样声明 String/double 类型。
    # 但运行时仍有类型：字符串不能直接和数字相加，类型提示也不会自动做转换。
    customer = "Alice"
    unit_price = 20.0
    quantities = [1, 2]
    total = unit_price * sum(quantities)

    # .2f 只控制显示为两位小数，不会把 float 变成精确的十进制金额。
    print(f"customer={customer} total={total:.2f}")
    print(f"grade={classify_score(82)} items={len(quantities)}")
    return 0


if __name__ == "__main__":
    # 直接运行才调用 main；被其他模块导入时不执行演示。退出码 0 表示成功。
    raise SystemExit(main())
