# 第 17 章：AI Agent 工程

**先修章节：** [第 5 章：异常处理](../05-exceptions/README.md)、[第 10 章：同步并发与异步并发](../10-concurrency-asyncio/README.md)、[第 11 章：自动化测试](../11-automated-testing/README.md)、[第 14 章：LLM 应用基础](../14-llm-application-basics/README.md)、[第 15 章：结构化输出与工具调用](../15-structured-output-tools/README.md)、[第 16 章：检索增强与对话记忆](../16-rag-memory/README.md)

AI Agent 是一个受控循环：模型提出下一步动作，应用执行允许的工具，结果作为观察回到模型，直到产生最终答案或预算耗尽。

## 学习目标

- 用联合类型建模工具调用、工具观察和最终答案，理解完整 Agent 状态机。
- 实现工具白名单、异常观察、步数上限和完整执行轨迹。
- 识别生产 Agent 的权限、预算、人工审批、可恢复执行和评测要求。

## Java 对照

### 对照卡：Agent 循环与工作流引擎 {#compare-agent-loop}

- 共同用途：根据当前状态选择下一动作，执行后更新状态，直到流程结束。
- 可验证行为差异：传统工作流转移由代码预定义；Agent 的候选动作由概率模型决定，但执行规则仍必须由代码控制。
- Python 适用场景：多步研究、跨系统业务协助、代码操作和动态任务分解。
- Java 开发者常见误区：把 Agent 当成一次更长的 Prompt，或让模型直接拥有无限工具、时间和权限。
- 修正方式：把模型限制为决策端口，循环设置预算，工具使用最小权限，高风险动作进入人工审批。

```java
while (budget.hasNext()) {
    Action action = model.next(history);
    history.add(executor.executeAllowed(action));
}
```

```python
# 不确定决策留给模型；确定性循环负责预算、白名单、执行和审计。
for step in range(1, max_steps + 1):
    action = model.next_action(tuple(history))
    if isinstance(action, FinalAnswer):
        return AgentResult(action.text, tuple(history), step)
```

## Python 知识

### 最小状态机

1. 组装目标、策略、可用工具和经过筛选的上下文。
2. 模型返回 `ToolCall` 或 `FinalAnswer`。
3. 应用验证工具名、参数、权限、预算和是否需要人工确认。
4. 执行工具，把成功或错误封装成 `ToolObservation`。
5. 将观察加入历史，再次请求动作；达到上限仍未结束则失败。

### 生产安全边界

- 工具最小权限：读写分离，默认只读，高风险写操作单独授权。
- 多重预算：步数、总时间、模型用量、工具调用次数和费用都有限制。
- 提示注入防护：检索文档和工具结果都是不可信数据，不能覆盖系统策略。
- 可恢复执行：为每次运行和工具调用分配 ID，持久化确定性状态，避免失败后重复副作用。
- 人工参与：付款、删除、外发消息和权限变更等动作必须在执行前展示影响并确认。
- 可观测与评测：记录动作类型、延迟、结果状态和错误代码；用固定任务集评估成功率、安全违规和成本。

并非所有任务都需要 Agent。步骤固定、规则明确的业务优先普通工作流；只有下一步确实依赖开放式上下文时，Agent 的动态决策才有价值。

## 可运行示例

### 示例：ch17-agent

[ch17_agent.py](examples/ch17_agent.py) 实现完整离线 Agent：`DemoModel` 先提出 `add` 工具调用，循环执行后记录观察，模型再返回最终答案。运行：`python -m tools.run_example --chapter 17`。

示例没有网络、API Key 或隐藏框架，因此可以单步调试每个状态。接入真实模型时只需替换 `AgentModel` 适配器，不改变安全循环。

## 练习

- `CH17-EX01`：[实现 run_agent](exercises/exercise_ch17.py)，支持最终答案、工具观察、未知工具拒绝、工具异常和步数上限。

先实现成功路径，再处理未知工具与死循环。完成后运行 `python -m tools.check_exercise --chapter 17`，最后查看带设计注释的[参考答案](../../solutions/ch17_agent.py)。

## 验证方式

示例应输出 `tool=add result=5` 和 `final=2 + 3 = 5 steps=2`。练习检查覆盖正常两步结束、未知高风险工具拒绝、无限循环截断和非法预算。

可额外运行 `python -m tools.check_exercise --chapter 17 --solution` 验证本章参考答案；完成后继续学习[第 18 章：Agent Harness 与循环工程](../18-agent-harness-loop/README.md)，把最小循环提升为可暂停恢复的运行时。

## 章节总结

可靠 Agent 的核心不是更复杂的提示词，而是清楚分离概率决策与确定性控制。模型负责建议，应用负责权限、验证、预算、执行、审计和最终安全责任。
