# 第 8 章：类型提示

**先修章节：** [第 3 章：函数与装饰器](../03-functions-decorators/README.md)、[第 4 章：面向对象与数据类](../04-oop-dataclasses/README.md)、[第 6 章：模块与包](../06-modules-packages/README.md)

## 学习目标

- 为函数、集合、联合类型和可选值编写准确类型提示。
- 使用 `TypeVar` 表达输入与输出之间的类型关系。
- 使用 `Protocol` 定义结构化接口，并理解静态检查与运行时校验的边界。

## Java 对照

### 对照卡：接口与 Protocol {#compare-typing-protocols}

- 共同用途：表达调用方依赖的能力，并在运行前发现不兼容调用。
- 可验证行为差异：Python 类型提示默认不强制运行时行为，`Protocol` 无需类显式声明实现关系。
- Python 适用场景：公共 API、依赖倒置、领域模型和大型重构。
- Java 开发者常见误区：以为写了 `str` 注解后运行时一定拒绝整数，或到处使用 `Any` 绕开错误。
- 修正方式：把 mypy 放入持续验证；外部数据在边界解析，内部代码依靠精确类型流动。

```java
interface Priced {
    BigDecimal price();
}
```

```python
class Priced(Protocol):
    @property
    def price(self) -> Decimal: ...
```

## Python 知识

优先使用内置泛型写法，如 `list[str]`、`dict[str, int]` 和 `str | None`。如果返回类型依赖输入元素类型，使用 `TypeVar`，而不是用 `object` 或 `Any` 擦除关系。

`Protocol` 关注“对象能做什么”，类似静态版本的鸭子类型。类型检查器不是数据校验器：JSON、环境变量和 HTTP 输入仍需在运行时解析和验证。

## 可运行示例

### 示例：ch08-types

[ch08_types.py](examples/ch08_types.py) 让未继承公共基类的 `Product` 满足 `Priced` 协议。运行：`python -m tools.run_example --chapter 08`。

## 练习

- `CH08-EX01`：[实现 first_or_none](exercises/exercise_ch08.py)，保留任意可迭代对象的元素类型。

不要把输入标成 `list[Any]`，也不要为了取第一个元素而物化整个迭代器。

完成后运行 `python -m tools.check_exercise --chapter 08`；通过后再查看[参考答案](../../solutions/ch08_types.py)。

## 验证方式

示例输出应包含 `typed_total=30.00`；练习检查会确认泛型函数不多消费迭代器，`python -m mypy learning tools` 应无类型错误。

## 章节总结

类型提示是可执行工具链中的设计文档。精确的泛型关系和小型协议能保留 Python 灵活性，同时提供接近静态语言的重构反馈。
