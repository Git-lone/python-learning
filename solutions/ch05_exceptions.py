"""CH05-EX01 参考答案。"""


class InvalidQuantityError(ValueError):
    """数量不是合法正整数。"""


def require_positive_quantity(raw: str) -> int:
    try:
        quantity = int(raw)
    except ValueError as error:
        # 包装转换错误时保留 __cause__，调用方既能识别领域异常，也能追溯根因。
        raise InvalidQuantityError(f"invalid quantity: {raw}") from error
    # 非正数属于业务校验失败，不需要人为制造一个底层转换异常。
    if quantity < 1:
        raise InvalidQuantityError("quantity must be positive")
    return quantity
