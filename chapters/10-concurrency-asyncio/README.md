# 第 10 章：同步并发与异步并发

**先修章节：** [第 3 章：函数与装饰器](../03-functions-decorators/README.md)、[第 5 章：异常处理](../05-exceptions/README.md)、[第 9 章：迭代器与生成器](../09-iterators-generators/README.md)

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 按 I/O 密集、CPU 密集和共享状态特征选择协程、线程或进程。
- 使用 `async`、`await`、`TaskGroup` 和 `asyncio.run` 管理协程生命周期。
- 正确处理并发上限、阻塞调用、取消和异常传播。

## Java 对照

### 对照卡：结构化并发 {#compare-structured-concurrency}

- 共同用途：让独立任务重叠执行，并在统一边界收集结果和失败。
- 可验证行为差异：`asyncio` 通常在单线程事件循环中协作调度，协程只会在 `await` 等让出点切换。
- Python 适用场景：大量网络或磁盘等待、异步客户端和高并发服务。
- Java 开发者常见误区：把协程等同于线程，直接调用阻塞 SDK 导致整个事件循环停顿。
- 修正方式：异步路径使用可等待 API；无法避免的阻塞函数用 `asyncio.to_thread` 隔离。

```java
var result = CompletableFuture.allOf(first, second).join();
```

```python
async with asyncio.TaskGroup() as group:
    first = group.create_task(load_first())
    second = group.create_task(load_second())
```

## Python 知识

调用 `async def` 只创建协程对象，必须 `await` 或创建任务才会执行。`TaskGroup` 把子任务生命周期限制在代码块中：退出前等待全部任务，失败时取消兄弟任务并传播异常组。

I/O 密集任务适合协程或线程；纯 Python CPU 密集工作通常需要进程或能释放 GIL 的原生库。生产代码还应设置超时，并确保取消时释放连接和锁。

### 教案：并发的收益和边界（建议 35 分钟）

1. **场景导入（5 分钟）：** 三个独立网络请求都要等待响应。先估计串行与并发的完成时间，再指出 CPU 密集计算为什么未必能用相同方法加速。
2. **追踪示例（10 分钟）：** 找出协程创建、`TaskGroup` 启动、`to_thread` 包装阻塞函数的边界；区分“创建协程对象”与“让它执行”。
3. **故障推演（10 分钟）：** 假设一个子任务失败，预测其他子任务与主调用会怎样结束。解释为什么同步阻塞函数直接放进事件循环会拖慢其他协程。
4. **练习与自测（10 分钟）：** 用信号量限制同时运行的任务数，但结果保持输入顺序。自测：任务失败后只返回已有结果是否满足要求？不满足；需要让失败传播并清理其他任务。

## 可运行示例

### 示例：ch10-concurrency

[ch10_concurrency.py](examples/ch10_concurrency.py) 在一个 `TaskGroup` 中组合协程与 `to_thread`。运行：`python -m tools.run_example --chapter 10`。

## 练习

- `CH10-EX01`：[实现 run_limited](exercises/exercise_ch10.py)，用 `Semaphore` 限制并发并保持输入顺序。

先拒绝小于 1 的限制；确保任一任务失败时其他任务不会泄漏到函数返回之后。

完成后运行 `python -m tools.check_exercise --chapter 10`；通过后再查看[参考答案](../../solutions/ch10_concurrency.py)。

## 验证方式

示例输出应包含 `results=['sync-A', 'async-B']` 和 `event_loop=closed`。练习检查用计数器验证并发峰值，同时检查结果顺序与非法限制。

## 章节总结

并发不是自动提速。先识别等待类型，再选择模型；结构化任务生命周期、并发上限与取消清理比“启动更多任务”更重要。
