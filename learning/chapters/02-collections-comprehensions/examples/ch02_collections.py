"""集合、切片、集合去重和推导式。"""


def main() -> int:
    orders = [
        ("DE", 120, True),
        ("FR", 78, True),
        ("DE", 42, False),
    ]
    paid_total = sum(amount for _, amount, paid in orders if paid)
    paid_countries = sorted({country for country, _, paid in orders if paid})
    even_squares = {number: number**2 for number in range(1, 7) if number % 2 == 0}

    print(f"paid_total={paid_total} countries={','.join(paid_countries)}")
    print(f"even_squares={even_squares}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
