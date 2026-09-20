"""函数是一等对象：闭包与保留元数据的装饰器。"""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

# ParamSpec 保留参数列表的类型关系，TypeVar 保留返回类型，供静态检查器使用。
P = ParamSpec("P")
R = TypeVar("R")


def trace(function: Callable[P, R]) -> Callable[P, R]:
    """打印调用结果，同时保持被装饰函数的签名。"""

    # wraps 保留名称、文档等元数据；*args 和 **kwargs 分别转发位置参数与关键字参数。
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        result = function(*args, **kwargs)
        print(f"{function.__name__}{args}->{result}")
        return result

    return wrapper


def make_multiplier(factor: int) -> Callable[[int], int]:
    """返回捕获 factor 的闭包。"""

    # 外层调用结束后，返回的函数仍能访问捕获的 factor，这就是闭包。
    def multiply(value: int) -> int:
        return factor * value

    return multiply


# 定义时相当于 add = trace(add)，以后调用 add 才会进入 wrapper。
@trace
def add(left: int, right: int) -> int:
    return left + right


def main() -> int:
    add(2, 3)
    print(f"scaled={make_multiplier(4)(5)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
