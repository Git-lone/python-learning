# 第 5 章：异常处理

**先修章节：** [第 1 章：基础语法](../01-basics/README.md)、[第 3 章：函数与装饰器](../03-functions-decorators/README.md)

## 学习目标

- 只捕获能够处理的具体异常，并区分预期失败与编程错误。
- 定义领域异常，使用 `raise ... from ...` 保留底层根因。
- 理解 `else` 与 `finally` 的执行时机，保证清理逻辑可靠发生。

## Java 对照

### 对照卡：异常转换 {#compare-exception-chaining}

- 共同用途：报告失败，并把错误传播给能够恢复或记录的层。
- 可验证行为差异：Python 没有受检异常，`raise NewError(...) from error` 会显式建立异常链。
- Python 适用场景：把解析、网络和存储异常转换为稳定的领域异常。
- Java 开发者常见误区：捕获宽泛的 `Exception` 后返回空值，导致错误现场消失。
- 修正方式：缩小 `try` 范围，只捕获目标异常，无法恢复时保留根因继续抛出。

```java
try {
    return Integer.parseInt(raw);
} catch (NumberFormatException ex) {
    throw new OrderInputException("invalid quantity", ex);
}
```

```python
try:
    return int(raw)
except ValueError as error:
    raise OrderInputError("invalid quantity") from error
```

## Python 知识

`try` 成功结束后才执行 `else`，无论成功失败都会执行 `finally`。如果资源对象支持上下文管理器，优先使用 `with`，因为它比手写 `finally` 更容易组合。

自定义业务异常通常继承 `ValueError`、`LookupError` 或项目级基类。异常消息应提供操作上下文，但不要泄露密钥、完整 SQL 或个人数据。

## 可运行示例

### 示例：ch05-exceptions

[ch05_exceptions.py](examples/ch05_exceptions.py) 把整数转换错误包装为订单输入错误，并验证 `finally` 清理。运行：`python -m tools.run_example --chapter 05`。

## 练习

- `CH05-EX01`：[实现正整数解析](exercises/exercise_ch05.py)，统一抛出 `InvalidQuantityError`。

字符串转换失败时保留 `ValueError` 为 `__cause__`；成功转换但数值小于 1 时直接抛出领域异常。

完成后运行 `python -m tools.check_exercise --chapter 05`；通过后再查看[参考答案](../../solutions/ch05_exceptions.py)。

## 验证方式

示例输出应包含 `handled=OrderInputError cause=ValueError` 和 `cleaned_up=True`。练习检查分别验证转换失败、非正数和正常值。

## 章节总结

异常是失败契约，不是普通分支。准确捕获、保留根因和可靠清理能让问题既对调用者有意义，也便于排查。
