"""CH05-EX01 参考答案。"""


class InvalidQuantityError(ValueError):
    """数量不是合法正整数。"""


def require_positive_quantity(raw: str) -> int:
    try:
        quantity = int(raw)
    except ValueError as error:
        raise InvalidQuantityError(f"invalid quantity: {raw}") from error
    if quantity < 1:
        raise InvalidQuantityError("quantity must be positive")
    return quantity
