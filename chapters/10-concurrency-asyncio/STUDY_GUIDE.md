# 第 10 章学案：asyncio 与并发限制

配合[本章讲解](README.md)使用，先画任务生命周期，再运行代码。

## asyncio 并发是什么

`asyncio` 用事件循环调度协程。协程在 `await` 等待 I/O 时让出执行权，其他任务可以继续；它不是“一个请求一个线程”。调用 `async def` 只得到协程对象，必须等待它或交给任务组调度。`TaskGroup` 管理一组子任务的生命周期，失败时取消仍未完成的同组任务。

## 组成与使用场景

本章使用标准库 `asyncio` 的 `TaskGroup`、`Semaphore`、`to_thread`。多个独立网络请求、模型流和数据库 I/O 可能受益于并发；纯 Python CPU 密集工作并不会仅因加 `async` 就加速。同步阻塞调用会占住事件循环，适合的阻塞 I/O 可以用 `to_thread` 移走。

并发还要控制资源：若同时创建数千个请求，可能打满连接池或触发限流。`Semaphore` 限制同时在执行的数量；失败、取消和超时要传播并清理，不能只返回部分成功结果。

## 代码怎样工作

[示例](examples/ch10_concurrency.py)在一个 `TaskGroup` 中启动异步标签和移到线程的同步标签，退出组后按固定顺序读取结果。[练习](exercises/exercise_ch10.py)对每个任务先获取信号量、运行工作、释放信号量，最终输出仍按输入顺序排列。

## 课前热身

- Java 线程池的任务提交与等待有什么区别？
- `async def` 调用后立刻执行函数体吗？什么时候真正执行？

## 探究任务

1. 阅读[示例](examples/ch10_concurrency.py)，分别圈出协程、`TaskGroup` 和 `to_thread`。预测两个任务的完成顺序与最终结果顺序是否一定相同：________。
2. 运行 `python -m tools.run_example --chapter 10`。记录结果和事件循环关闭状态：________。
3. 推演一个子任务失败时，另一个未结束子任务会怎样；解释同步阻塞 I/O 为什么要移出事件循环：________。

## 动手完成

- 实现[练习](exercises/exercise_ch10.py)的 `run_limited`，用 `Semaphore` 控制同时运行数，并保持输入结果顺序。
- 运行 `python -m tools.check_exercise --chapter 10`。记录 `limit=1`、小于 1 与任务失败时的行为：________。

## 过关自检

- 能区分等待 I/O 与消耗 CPU 的工作。
- 能解释取消传播与任务清理的重要性。
- 能说明并发完成顺序不等于结果顺序。完成后再看[参考答案](../../solutions/ch10_concurrency.py)。
