# 第 19 章：真实模型 SDK 与流式边界

先修：第 10、13、14 章。所有命令在项目根目录 `C:\workspace\my\py\learning` 执行，使用项目虚拟环境的 Python。

### 本章要做成什么

让同一调用方既能使用离线 fixture，也能接入真实 OpenAI Responses API；明确区分增量文本、完成、失败和输出截断。不会因为收到几个字符就把任务记为成功。

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 统一模型调用边界并区分部分输出和完成输出。
- async for 消费事件，仅在 completed 后记为成功。
- 完成“解析真实 usage，拒绝伪造零用量”并解释失败测试的意义。

## Java 对照

### 真实模型 SDK 与流式边界 {#compare-model-sdk}

- 共同用途：统一模型调用边界并区分部分输出和完成输出。
- 可验证行为差异：Python async generator 必须异步消费；Java 常以响应式流或回调表达。
- Python 适用场景：异步 token 流、限时调用和 provider 适配。
- Java 开发者常见误区：直接 join 异步生成器，或把 EOF 当成功。
- 修正方式：async for 消费事件，仅在 completed 后记为成功。



`Gateway` 对应服务接口，`OpenAIGateway` 对应 SDK 适配器；`async for` 消费异步流，可类比响应式订阅。它不是普通 `Iterator`，不能直接传给 `str.join`。用异步列表推导式收集，或边接收边转发。

## Python 知识

### 沿代码读一遍

1. [gateway.py](../../agent_lab/gateway.py) 中的 `Event` 是内部协议，不把供应商事件对象扩散到业务层。
2. `OfflineGateway` 只回显证据，用量保持 `None`；它没有推理能力，也不估算 token。
3. `OpenAIGateway` 设置输出上限和整体时间预算，显式关闭流；`response.incomplete`、失败和缺少完成事件都报错。
4. [model_demo.py](../../agent_lab/model_demo.py) 默认离线，只有 `--live` 才创建真实客户端，SDK 自动重试设为 0，避免教学例子里产生隐式重复请求。
5. [SDK 测试](../../tests/test_gateway.py) 使用真实 SDK 加 HTTPX2 的 mock transport 解析 SSE，没有调用远端模型。

### 运行与观察

### 教案：把模型 SDK 当成不可靠外部依赖（建议 40 分钟）

1. **先约定结果（5 分钟）：** 一次文本流可能产生若干片段，但只有收到完成事件才可宣布成功。先预测“已有部分文字，随后连接中断”应该返回答案还是报错。
2. **沿边界读代码（10 分钟）：** 对照 `OfflineGateway` 和 `OpenAIGateway`：两者返回同一个内部 `Event`，但只有后者接触 SDK。标出输出上限、截止时间、流关闭和用量可能为 `None` 的位置。
3. **运行与故障观察（10 分钟）：** 运行离线示例，再看 mock transport 测试怎样模拟 SSE 完成、缺少完成事件和超时。把 SDK 自动重试为 0 与应用总预算联系起来。
4. **练习（10 分钟）：** 先将正常整数用量解析为二元组，再覆盖缺字段、字符串、负数和 `bool`。自测：`isinstance(True, int)` 为真，为什么仍须拒绝？布尔值不是可用的 token 计数。
5. **复盘（5 分钟）：** 口头区分“模型生成过片段”“模型完整结束”“应用任务完成”三个事件；它们不能互相代替。

## 可运行示例

### 运行记录：ch19-demo

```powershell
python -m tools.run_example --chapter 19
python -m pytest tests/test_gateway.py -q
```

预期输出包含 `OFFLINE evidence:`。可选真实调用前，自行在当前进程配置 `OPENAI_API_KEY` 和账户可用的 `OPENAI_MODEL`，然后运行：

```powershell
python -m agent_lab.model_demo --live
```

这一步可能计费；不要将密钥写进代码、日志或提交记录。没有配置时应明确报错，不能悄悄切回离线并声称调用成功。当前示例只发送代码内的合成资料。

## 练习

完成 [exercise_ch19.py](exercises/exercise_ch19.py) 的 `parse_usage`：返回输入/输出 token 二元组；字段缺失、字符串数字、布尔值、负数均抛 `ValueError`，合法的 0 保留。注意 Python 中 `bool` 是 `int` 的子类。

```powershell
python -m tools.check_exercise --chapter 19
python -m tools.check_exercise --chapter 19 --solution
```

[参考答案](../../solutions/ch19_model_sdk.py)。进一步实验：人为丢掉完成事件、模拟超时，观察为什么部分文本不能等价于最终结果。

### 面试追问

- SDK 超时和整个 Agent 超时有什么区别？前者限制一次网络调用，后者还要包含检索、工具、重试和等待。
- 重试应该放哪一层？明确唯一责任层，总尝试数有上限；已经输出的流不能直接无条件重放。
- 怎样减少幻觉？数据权限和证据约束是起点，但提示词并不保证正确；还需要拒答策略、引用验证、固定评测集。

API 依据：[OpenAI Python SDK](https://github.com/openai/openai-python)、[流式响应文档](https://developers.openai.com/api/docs/guides/streaming-responses)。代码版本见根目录 `pyproject.toml`；本章只实现文本流，没有把模型工具调用片段自动接入第 17 章循环。

## 验证方式

运行 `python -m tools.check_exercise --chapter 19` 验证自己的实现，`--solution` 用于核对参考答案。示例合同由 `python -m tools.run_example --chapter 19` 验证；工程异常测试见根目录 tests。

## 章节总结

async for 消费事件，仅在 completed 后记为成功。面试时同时说明实现、测试证据和未实现边界；公开原帖与自编练习分别见 [真实面经](../../career/INTERVIEW_EXPERIENCES.md) 和 [面试练习](../../career/INTERVIEW_PRACTICE.md)。
