"""自定义异常、异常链和 finally。"""


class OrderInputError(ValueError):
    """订单输入无法转换为领域值。"""


def parse_quantity(raw: str) -> int:
    try:
        quantity = int(raw)
    except ValueError as error:
        raise OrderInputError(f"invalid quantity: {raw}") from error
    if quantity <= 0:
        raise OrderInputError("quantity must be positive")
    return quantity


def main() -> int:
    cleaned_up = False
    try:
        parse_quantity("three")
    except OrderInputError as error:
        print(f"handled={type(error).__name__} cause={type(error.__cause__).__name__}")
    finally:
        cleaned_up = True
    print(f"cleaned_up={cleaned_up}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
