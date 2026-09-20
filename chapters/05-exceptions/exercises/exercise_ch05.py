"""练习：把底层转换异常包装为领域异常。"""


class InvalidQuantityError(ValueError):
    """数量不是合法正整数。"""


def require_positive_quantity(raw: str) -> int:
    """解析正整数；失败时抛出 InvalidQuantityError 并保留异常链。"""
    # 区分文本不能转整数与整数非正两种失败；转换失败时保留原异常作为原因。
    raise NotImplementedError("请完成 CH05-EX01")
