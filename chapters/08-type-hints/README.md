# 第 8 章：类型提示

**先修章节：** [第 3 章：函数与装饰器](../03-functions-decorators/README.md)、[第 4 章：面向对象与数据类](../04-oop-dataclasses/README.md)、[第 6 章：模块与包](../06-modules-packages/README.md)

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

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

读类型提示时，先把符号翻成一句话：`list[str]` 是“元素为字符串的列表”，`dict[str, int]` 是“键为字符串、值为整数的字典”，`str | None` 是“字符串或空值”。最后一个不是 Java 的 `Optional<String>` 包装对象；有值时拿到的就是字符串，没有值时才是 `None`。

本章练习把这些符号组合成 `first_or_none(items: Iterable[T]) -> T | None`。这里的 `T` 是用 `TypeVar` 声明的**类型占位符**，用途像 Java 泛型方法的 `<T>`：输入元素与非空返回值共用同一个类型，而不是说“返回什么都行”。传入 `["DE", "FR"]` 得到 `"DE"`，传入空列表得到 `None`。对一个是否为空还未知的字符串列表，调用方应先用 `if value is not None:` 排除空值，再调用 `value.lower()`。

示例中的 `Protocol` 则描述**传进来的对象要有什么能力**：`total_price` 只读 `item.price`，所以 `Product` 有一个类型为 `Decimal` 的 `price` 字段就够了，不必写 Java 式的 `implements Priced`。反过来，`{"price": "25.50"}` 不是同一种结构：字典的键不是对象属性，字符串也不是 `Decimal`。类型检查器可以指出这种不匹配，却不会替你把 JSON 转成商品对象。

### 教案：先定义行为，再写类型（建议 35 分钟）

1. **场景导入（5 分钟）：** 两个商品类没有共同父类，但都能提供价格。先写出调用方真正需要的属性或方法，再判断是否必须要求继承同一基类。
2. **读示例（10 分钟）：** 找到 `Priced` 协议及 `Product` 的对应成员。解释结构化匹配与 Java 显式 `implements` 的差异，并指出 `mypy` 检查发生在何时。
3. **运行与检查（10 分钟）：** 运行示例，再运行 `python -m mypy`。思考把外部 JSON 标注为某个类型后，为什么仍可能在运行时得到非法值。
4. **练习与自测（10 分钟）：** `first_or_none` 应保留输入元素类型，并只取第一个元素。自测：对生成器调用 `list()` 再取首项有什么问题？它提前消费全部数据，丢失惰性优势。

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
