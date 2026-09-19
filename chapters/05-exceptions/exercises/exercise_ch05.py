"""练习：把底层转换异常包装为领域异常。"""


class InvalidQuantityError(ValueError):
    """数量不是合法正整数。"""


def require_positive_quantity(raw: str) -> int:
    """解析正整数；失败时抛出 InvalidQuantityError 并保留异常链。"""
    raise NotImplementedError("请完成 CH05-EX01")
