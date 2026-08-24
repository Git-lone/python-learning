"""Protocol、泛型集合与静态类型检查。"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


class Priced(Protocol):
    @property
    def price(self) -> Decimal: ...


@dataclass(frozen=True)
class Product:
    name: str
    price: Decimal


def total_price(items: Iterable[Priced]) -> Decimal:
    return sum((item.price for item in items), start=Decimal("0"))


def main() -> int:
    products = [Product("book", Decimal("25.50")), Product("pen", Decimal("4.50"))]
    print(f"typed_total={total_price(products)}")
    print("protocol=structural")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
