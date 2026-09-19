# 第 4 章：面向对象与数据类

**先修章节：** [第 1 章：基础语法](../01-basics/README.md)、[第 3 章：函数与装饰器](../03-functions-decorators/README.md)

## 学习目标

- 使用类、实例属性和方法表达领域行为，而不是照搬 JavaBean 模板。
- 使用 `dataclass`、`field(default_factory=...)`、`frozen` 和 `slots` 创建数据对象。
- 通过属性与特殊方法接入 Python 的运算符和容器协议。

## Java 对照

### 对照卡：数据类与值对象 {#compare-oop-dataclasses}

- 共同用途：把相关状态和行为组织成领域对象，并支持比较和显示。
- 可验证行为差异：Python `dataclass` 自动生成初始化与比较方法，公开属性通常可直接访问。
- Python 适用场景：值对象、命令、事件、配置和轻量领域模型。
- Java 开发者常见误区：为每个字段机械创建 getter/setter，或把可变列表直接作为类级默认值。
- 修正方式：默认保持模型简单；计算属性用 `property`，可变默认值用 `default_factory`。

```java
record OrderLine(String sku, BigDecimal price, int quantity) {}
```

```python
@dataclass(frozen=True, slots=True)
class OrderLine:
    sku: str
    unit_price: float
    quantity: int = 1
```

## Python 知识

实例方法的第一个参数通常命名为 `self`，它是显式传入的实例引用。单下划线表示内部实现约定，双下划线触发名称改写，但 Python 并不依靠访问修饰符构建绝对封装。

`__len__`、`__iter__`、`__str__` 等特殊方法让对象参与语言协议。优先组合而非深继承；只有确实存在可替换的 “is-a” 关系时才使用继承。

## 可运行示例

### 示例：ch04-oop

[ch04_oop.py](examples/ch04_oop.py) 创建不可变订单行和包含计算属性的订单。运行：`python -m tools.run_example --chapter 04`。

## 练习

- `CH04-EX01`：[实现 Money 值对象加法](exercises/exercise_ch04.py)。

同币种相加应返回新对象；币种不同必须抛出 `ValueError`。保持 `Money` 不可变，不要修改任一操作数。

完成后运行 `python -m tools.check_exercise --chapter 04`；通过后再查看[参考答案](../../solutions/ch04_oop.py)。

## 验证方式

示例输出应包含 `order=SO-1001 lines=2 total=55.00`。练习检查自动验证相加结果、不可变性和跨币种失败。

## 章节总结

Python 面向对象强调协议和简单对象，而非样板代码。数据类适合承载数据，特殊方法适合接入语言行为，领域约束仍应由清晰的方法维护。
