"""数据类、属性和特殊方法。"""

from dataclasses import dataclass, field


# dataclass 生成初始化与比较方法；frozen 禁止字段重新赋值，slots 限制动态加属性。
# frozen 不等于深度不可变：若字段是列表，列表内容仍可能被修改。
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
    # 每个订单创建自己的列表，不能让多个实例共享一个可变默认值。
    lines: list[OrderLine] = field(default_factory=list)

    @property
    def total(self) -> float:
        # 以属性方式访问，但每次读取都会重新计算，不是缓存字段。
        return sum(line.subtotal for line in self.lines)

    def __len__(self) -> int:
        return len(self.lines)


def main() -> int:
    order = Order("SO-1001", [OrderLine("BOOK", 25.0, 2), OrderLine("PEN", 5.0)])
    print(f"order={order.order_id} lines={len(order)} total={order.total:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
