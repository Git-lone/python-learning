# 第 13 章：HTTP API 与可靠性

**先修章节：** [第 5 章：异常处理](../05-exceptions/README.md)、[第 7 章：文件与上下文管理器](../07-files-context-managers/README.md)、[第 8 章：类型提示](../08-type-hints/README.md)、[第 10 章：同步并发与异步并发](../10-concurrency-asyncio/README.md)、[第 12 章：配置、命令行与日志](../12-configuration-cli-logging/README.md)

模型 API、搜索工具和向量服务本质上都是远程边界。本章先学习不依赖任何厂商 SDK 的 HTTP 可靠性原则。

## 学习目标

- 显式设置 HTTP 超时，并区分网络失败、HTTP 状态失败和响应解析失败。
- 只对可恢复、幂等的操作执行有限重试，避免故障放大。
- 把 JSON 响应当作不可信输入，在边界完成结构和字段校验。

## Java 对照

### 对照卡：远程调用边界 {#compare-http-resilience}

- 共同用途：向远程服务发送请求，校验响应并转换为领域结果。
- 可验证行为差异：Python 标准库响应对象可由 `with` 管理；网络、状态码和 JSON 解析具有不同异常类型。
- Python 适用场景：模型推理、Embedding、搜索、内部微服务和 Agent 工具。
- Java 开发者常见误区：从同步 HTTP 客户端照搬“捕获 Exception 后立即重试”，忽略幂等性与总时间预算。
- 修正方式：为每个调用定义超时、可重试错误集合、最大次数、退避策略和幂等键。

```java
var request = HttpRequest.newBuilder(uri)
    .timeout(Duration.ofSeconds(2))
    .GET()
    .build();
```

```python
with urlopen(url, timeout=2) as response:
    payload = json.loads(response.read().decode("utf-8"))
```

## Python 知识

超时不是可选优化，而是远程调用契约。一次完整操作通常还需要总截止时间；即使单次请求设置两秒，三次重试也可能超过业务预算。写操作若没有幂等键，自动重试可能产生重复副作用。

响应进入领域层前要验证：状态码、媒体类型、字符编码、JSON 根类型、必填字段和数值范围。模型 SDK 只是更方便的 HTTP 客户端，不能替代这些边界设计。

## 可运行示例

### 示例：ch13-http-api

[ch13_http_api.py](examples/ch13_http_api.py) 在随机本地端口启动标准库 HTTP 服务，客户端用显式超时读取 JSON，并在 `finally` 中关闭服务。运行：`python -m tools.run_example --chapter 13`。

## 练习

- `CH13-EX01`：[实现 load_json_with_retry](exercises/exercise_ch13.py)，只重试 `TimeoutError` 并要求 JSON 根节点为对象。

`retries=1` 表示首次尝试之外最多再试一次。完成后运行 `python -m tools.check_exercise --chapter 13`，再查看[参考答案](../../solutions/ch13_http_api.py)。

## 验证方式

示例应输出 HTTP 200 和两条目录数据。练习检查覆盖恢复成功、预算耗尽、非法 JSON、数组根节点和负重试次数。

## 章节总结

可靠远程调用来自明确预算和窄重试条件，不来自“多试几次”。先建立稳定 HTTP 边界，再接入任何 LLM 或 Agent 工具 SDK。
