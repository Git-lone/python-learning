"""Protocol、泛型集合与静态类型检查。"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


# 结构化接口：Product 只要具有兼容的 price 属性，就不必显式继承 Priced。
# 类型提示主要供 IDE/mypy 检查，不会自动在运行时拦截错误输入。
class Priced(Protocol):
    """描述调用方需要的只读价格属性，而非要求实现类继承某个业务基类。"""

    @property
    def price(self) -> Decimal: ...


@dataclass(frozen=True)
class Product:
    """用 Decimal 保存商品价格；字段已满足 Priced 协议，无需显式 implements。"""

    name: str
    price: Decimal


def total_price(items: Iterable[Priced]) -> Decimal:
    """一次遍历汇总所有对象的价格，空输入返回 Decimal 零值。

    依赖的是 price 属性而非 Product 具体类，其他符合协议的对象也能参与汇总。
    """

    # 指定 Decimal 起始值，空集合也返回 Decimal，而不是 sum 默认的整数 0。
    return sum((item.price for item in items), start=Decimal("0"))


def main() -> int:
    # 从字符串构造 Decimal，避免先经过 float 引入二进制小数误差。
    products = [Product("book", Decimal("25.50")), Product("pen", Decimal("4.50"))]
    print(f"typed_total={total_price(products)}")
    print("protocol=structural")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
