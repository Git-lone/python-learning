# 第 11 章：自动化测试

**先修章节：** [第 3 章：函数与装饰器](../03-functions-decorators/README.md)、[第 5 章：异常处理](../05-exceptions/README.md)、[第 6 章：模块与包](../06-modules-packages/README.md)、[第 8 章：类型提示](../08-type-hints/README.md)

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 使用普通测试函数和 `assert` 编写快速、独立、可读的单元测试。
- 使用参数化、夹具和 `pytest.raises` 覆盖等价类与边界。
- 区分替身对象的用途，避免过度模拟实现细节。

## Java 对照

### 对照卡：pytest 与 JUnit {#compare-pytest-tests}

- 共同用途：自动验证正常路径、边界行为和异常契约，防止回归。
- 可验证行为差异：pytest 使用普通 `assert`、函数夹具和参数化收集测试，不要求测试类和生命周期注解。
- Python 适用场景：单元、组件、接口和端到端测试，并可逐层复用夹具。
- Java 开发者常见误区：逐字照搬 JUnit 测试类结构，或为了达到覆盖率而断言内部调用次数。
- 修正方式：默认使用小测试函数，按可观察行为断言，只在真正的外部边界使用 mock。

```java
@ParameterizedTest
@CsvSource({"100, 0.2, 80.00", "19.99, 0, 19.99"})
void discounts(String price, String rate, String expected) { /* ... */ }
```

```python
@pytest.mark.parametrize(
    ("price", "rate", "expected"),
    [("100", "0.2", "80.00"), ("19.99", "0", "19.99")],
)
def test_discount(price: str, rate: str, expected: str) -> None:
    ...
```

## Python 知识

### 两个测试函数，为什么会得到三个测试结果？

先按 Arrange / Act / Assert 读一个测试：准备金额，调用折扣函数，最后比较实际与预期金额。参数化只是换掉第一步的数据，后两步的行为不变。

看上面的 `@pytest.mark.parametrize`：第一行数据把参数分别设为价格 `"100"`、减免比例 `"0.2"`、折后金额 `"80.00"`，第二行换成原价不打折。**参数化**就是让测试框架用每行数据各运行一次同一个函数，像 JUnit 的 `@ParameterizedTest`；它不是在一个测试里循环两次。即使第一行失败，第二行仍是独立的用例。在[本章示例](examples/test_pricing.py)里，这两行加上独立的负价格测试，一共三个。

负价格用例的断言不在等号右边，而在 `with pytest.raises(ValueError, match="negative"):`。类比 JUnit 的 `assertThrows`：代码块必须抛出指定类型或其子类；额外的 `match` 要求异常消息匹配正则。只写 `pytest.raises(ValueError)` **不会**检查消息。如果函数把负数悄悄改为零并正常返回，这条测试反而失败。

**夹具（fixture）**解决另一个问题：用例执行前从哪里拿到已准备好的资源？例如测试声明参数 `tmp_path`，pytest 就按名字提供它的临时目录，像 JUnit 的 `@TempDir`。这不是一行参数化测试数据。折扣函数只需要几个金额，不必为它引入夹具或 mock。

### 教案：测试可观察行为（建议 30 分钟）

1. **先写合同（5 分钟）：** 不看实现，列出“正常折扣”“边界折扣”“非法折扣”各一个输入和期望。把预期写成具体结果或异常，而不是“应该正确”。
2. **读测试（10 分钟）：** 在示例中逐项标记 Arrange、Act、Assert。说明参数化测试为何复用同一断言，夹具为何要承担建立与清理职责。
3. **运行观察（5 分钟）：** 运行示例，找到每个测试对应的业务规则。若临时把某条规则改错，预测哪些断言会失败；不要把同一错误公式复制到期望值里。
4. **完成练习（10 分钟）：** 先写“折扣超过价格时返回下限”的测试，再检查价格恰好等于折扣的边界。自测：只断言“不抛异常”是否足够？不够；还要断言实际金额。

## 可运行示例

### 示例：ch11-pytest

[test_pricing.py](examples/test_pricing.py) 测试 [percentage_discount](examples/sample/pricing.py) 的参数组合和异常边界。运行：`python -m tools.run_example --chapter 11`。

## 练习

- `CH11-EX01`：[补全折扣下限测试](exercises/exercise_ch11.py)，验证固定折扣不能把价格降到零以下。

使用清晰的 Arrange/Act/Assert，不要复制生产实现来计算期望值。

完成后运行 `python -m tools.check_exercise --chapter 11`；通过后再查看[参考答案](../../solutions/ch11_testing.py)。

## 验证方式

章节示例应报告 `3 passed`。统一练习检查器会执行你补写的测试，并额外确认真实边界结果为零。

## 章节总结

好测试描述行为而不是实现。代表性数据、边界、异常和清晰失败信息，比大量脆弱 mock 更能支撑重构。
