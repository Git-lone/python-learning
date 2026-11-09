# 第 3 章：函数与装饰器

**先修章节：** [第 1 章：基础语法](../01-basics/README.md)、[第 2 章：集合与推导式](../02-collections-comprehensions/README.md)

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 使用位置参数、关键字参数和默认值设计清晰的函数接口。
- 理解函数是一等对象，以及闭包如何保存外层作用域状态。
- 编写使用 `functools.wraps` 的装饰器，避免丢失函数元数据和签名。

## Java 对照

### 对照卡：高阶函数与装饰器 {#compare-functions-decorators}

- 共同用途：封装行为，并复用日志、鉴权或重试等横切逻辑。
- 可验证行为差异：Python 装饰器在定义阶段接收函数并替换原名称绑定；Java 注解本身通常不执行包装。
- Python 适用场景：轻量日志、缓存、重试、路由注册和参数校验。
- Java 开发者常见误区：认为 `@decorator` 只是元数据，忽略它会改变实际调用对象。
- 修正方式：把装饰器展开理解为 `function = decorator(function)`，并始终考虑异常和返回值传播。

```java
Function<Integer, Integer> multiplier(int factor) {
    return value -> factor * value;
}
```

```python
def make_multiplier(factor: int):
    def multiply(value: int) -> int:
        return factor * value
    return multiply
```

## Python 知识

参数顺序通常是普通位置参数、`*args`、仅限关键字参数和 `**kwargs`。默认值在函数定义时求值，因此不要把可变列表或字典作为默认值；改用 `None` 后在函数内部创建。

闭包保存自由变量。装饰器本质是高阶函数；通用装饰器可用 `ParamSpec` 和 `TypeVar` 保留参数与返回值类型，用 `@wraps` 保留名称、文档和测试工具需要的元数据。

### 教案：函数也是可传递的对象（建议 35 分钟）

1. **先想场景（5 分钟）：** Java 中可能创建一个携带折扣率的策略对象；Python 可以由工厂函数返回一个函数。先判断折扣率该在创建时校验，还是每次计算价格时校验。
2. **逐层追踪（10 分钟）：** 在示例里区分外层工厂、闭包保存的自由变量、被装饰函数和包装函数。解释为什么两次创建的闭包可以记住不同状态。
3. **观察行为（10 分钟）：** 运行示例后查看输出和被装饰函数的名称。思考去掉 `@wraps` 后，日志或测试读到的元数据会发生什么变化。
4. **练习与自测（10 分钟）：** 对 `0`、`1`、负数和大于 `1` 的折扣率分别写预期。自测：为什么不写 `def f(items=[])`？默认列表只创建一次，后续调用会共享并修改它。

## 可运行示例

### 示例：ch03-functions

[ch03_functions.py](examples/ch03_functions.py) 同时演示捕获状态的闭包和保留签名的跟踪装饰器。运行：`python -m tools.run_example --chapter 03`。

## 练习

- `CH03-EX01`：[实现 make_discount](exercises/exercise_ch03.py)，返回捕获折扣率的函数。

工厂应立即拒绝不在 `0..1` 的比例；返回函数接受价格并把结果四舍五入到两位小数。

完成后运行 `python -m tools.check_exercise --chapter 03`；通过后再查看[参考答案](../../solutions/ch03_functions.py)。

## 验证方式

示例输出应包含 `add(2, 3)->5` 和 `scaled=20`。练习检查覆盖闭包状态、舍入、合法端点和非法比例。

## 章节总结

把函数当作值后，策略、回调和横切逻辑都能用统一方式组合。装饰器能力很强，但应保持包装透明、异常可见和类型契约清楚。
