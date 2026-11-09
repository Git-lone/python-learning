# 第 4 章学案：数据类与值对象

配合[本章讲解](README.md)使用。先写不变量，再写对象方法。

## 数据类和值对象是什么

对象把数据与行为放在一起。`@dataclass` 根据字段生成初始化、比较等样板方法；值对象按内容表达意义，通常希望创建后不改变。例如 `Money(10, 'CNY')` 的币种是金额语义的一部分，不能只把两个数值相加。

## 组成与使用场景

本章的核心是 `dataclasses` 标准库、实例方法、`@property`、`frozen=True` 和 `field(default_factory=...)`。适合订单行、配置快照、领域结果这类字段明确的对象；需要复杂生命周期或可变聚合时，可以让外层对象持有若干不可变值对象。

`frozen=True` 阻止字段重新赋值，但不是深度冻结：字段若指向可变列表，列表内容仍能改变。`default_factory=list` 则保证每个订单拥有自己的明细列表。Java record 与此接近，但 Python 数据类的可变性需逐字段设计。

## 代码怎样工作

[示例](examples/ch04_oop.py)中每条 `OrderLine` 由单价和数量计算 `subtotal`；`Order.total` 读取订单行并求和，访问时才计算，不是缓存字段。[练习](exercises/exercise_ch04.py)让金额相加返回新对象，并在不同币种时抛错，从方法内部维护领域不变量。

## 课前热身

- Java record 与普通 Java 类在数据承载和可变性上有什么不同？
- 一个订单的总价由订单行得出，应保存为独立字段还是计算属性？说明取舍。

## 探究任务

1. 阅读[示例](examples/ch04_oop.py)，写出 `OrderLine.subtotal` 和 `Order.total` 的计算顺序。预测总价：________。
2. 运行 `python -m tools.run_example --chapter 04`。实际总价：________。指出 `frozen=True` 能阻止什么、不能阻止什么：________。
3. 设有 `Money(10, 'CNY')` 与 `Money(5, 'USD')`，先写出相加应发生什么，而不是直接编码：________。

## 动手完成

- 在[练习](exercises/exercise_ch04.py)实现同币种加法返回新对象、异币种抛异常。
- 运行 `python -m tools.check_exercise --chapter 04`。检查原操作数是否保持不变：________。

## 过关自检

- 能区分数据类自动生成的方法与自己写的业务规则。
- 能解释为什么 `default_factory=list` 比共享默认列表安全。
- 能指出值对象的不可变边界。完成后再看[参考答案](../../solutions/ch04_oop.py)。
