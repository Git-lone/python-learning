"""集合、切片、集合去重和推导式。"""


def main() -> int:
    orders = [
        ("DE", 120, True),
        ("FR", 78, True),
        ("DE", 42, False),
    ]
    # 元组按位置解包；_ 表示此处不用的值。生成器表达式不创建中间金额列表。
    paid_total = sum(amount for _, amount, paid in orders if paid)
    # set 去重但不保证顺序，再用 sorted 得到可重复的输出。
    paid_countries = sorted({country for country, _, paid in orders if paid})
    # range 的右端点不包含在内；字典推导式同时完成筛选和键值映射。
    even_squares = {number: number**2 for number in range(1, 7) if number % 2 == 0}

    print(f"paid_total={paid_total} countries={','.join(paid_countries)}")
    print(f"even_squares={even_squares}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
