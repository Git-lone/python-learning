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

测试采用 Arrange/Act/Assert 结构：准备数据、执行一个行为、断言可观察结果。参数化适合用同一规则验证多个代表值；夹具适合有建立和清理生命周期的共享资源，而不是隐藏所有输入。

`pytest.raises` 同时验证异常类型与消息。mock 应放在代码真正读取名称的位置，并优先使用 `autospec` 或严格接口，避免测试替身接受生产对象不支持的调用。

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
