"""自定义异常、异常链和 finally。"""


class OrderInputError(ValueError):
    """订单输入无法转换为领域值。"""


def parse_quantity(raw: str) -> int:
    try:
        quantity = int(raw)
    except ValueError as error:
        # 对外暴露业务异常，同时用 from 保留底层转换失败的原因，便于追踪。
        raise OrderInputError(f"invalid quantity: {raw}") from error
    # 能转换成整数不代表符合业务规则，这类失败没有底层转换异常。
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
        # 正常返回或抛异常都会经过 finally；真实资源通常优先交给 with 管理。
        cleaned_up = True
    print(f"cleaned_up={cleaned_up}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
