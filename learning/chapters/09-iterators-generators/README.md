# 第 9 章：迭代器与生成器

**先修章节：** [第 2 章：集合与推导式](../02-collections-comprehensions/README.md)、[第 3 章：函数与装饰器](../03-functions-decorators/README.md)

## 学习目标

- 区分可迭代对象与迭代器，理解 `iter`、`next` 和 `StopIteration`。
- 使用 `yield` 编写保存状态的惰性生成器。
- 识别一次性消费、无限序列和延迟异常等惰性求值边界。

## Java 对照

### 对照卡：惰性数据流 {#compare-iterators-generators}

- 共同用途：逐项处理数据，避免一次性把全部结果加载到内存。
- 可验证行为差异：Python `for` 自动驱动迭代器协议，含 `yield` 的函数调用后只创建生成器而不立即执行函数体。
- Python 适用场景：大文件、分页结果、流水线转换和无限序列。
- Java 开发者常见误区：像复用 `List` 一样重复消费生成器，或在创建生成器时期待立刻抛出验证异常。
- 修正方式：明确一次性语义，需要复用时物化；测试时实际推进迭代器。

```java
Stream<Integer> totals = Stream.iterate(seed, this::nextTotal);
```

```python
def running_totals(numbers):
    total = 0
    for number in numbers:
        total += number
        yield total
```

## Python 知识

可迭代对象能产生迭代器，迭代器在 `__next__` 中维护当前位置并在结束时抛出 `StopIteration`。生成器替你实现这些状态机细节，通常是自定义惰性序列的首选。

生成器表达式 `(transform(item) for item in source)` 不会立即创建列表。惰性可以节省内存，但错误也可能延迟到消费时发生；API 文档和测试应说明这一点。

## 可运行示例

### 示例：ch09-iterators

[ch09_iterators.py](examples/ch09_iterators.py) 手写倒计时迭代器，并用生成器计算运行总和。运行：`python -m tools.run_example --chapter 09`。

## 练习

- `CH09-EX01`：[实现 chunked](exercises/exercise_ch09.py)，把任意可迭代对象惰性切成固定大小列表。

保留不足一个完整块的尾部数据；`size < 1` 时抛出 `ValueError`。

完成后运行 `python -m tools.check_exercise --chapter 09`；通过后再查看[参考答案](../../solutions/ch09_iterators.py)。

## 验证方式

示例输出应包含 `countdown=[3, 2, 1]` 和 `running_totals=[2, 5, 10]`。练习检查覆盖尾块、空输入和非法块大小。

## 章节总结

迭代协议统一了容器、文件和生成器。惰性求值能降低内存占用并改善组合性，但调用方必须理解消费时机和一次性语义。
