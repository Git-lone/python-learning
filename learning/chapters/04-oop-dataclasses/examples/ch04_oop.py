"""数据类、属性和特殊方法。"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class OrderLine:
    sku: str
    unit_price: float
    quantity: int = 1

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity


@dataclass
class Order:
    order_id: str
    lines: list[OrderLine] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(line.subtotal for line in self.lines)

    def __len__(self) -> int:
        return len(self.lines)


def main() -> int:
    order = Order("SO-1001", [OrderLine("BOOK", 25.0, 2), OrderLine("PEN", 5.0)])
    print(f"order={order.order_id} lines={len(order)} total={order.total:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
