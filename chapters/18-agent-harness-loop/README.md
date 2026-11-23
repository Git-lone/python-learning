# 第 18 章：Agent Harness 与循环工程

**先修章节：** [第 7 章：文件与上下文管理器](../07-files-context-managers/README.md)、[第 11 章：自动化测试](../11-automated-testing/README.md)、[第 12 章：配置、命令行与日志](../12-configuration-cli-logging/README.md)、[第 17 章：AI Agent 工程](../17-ai-agent-engineering/README.md)

第 17 章实现了最小 Agent Loop。本章把循环提升为 Harness 工程：模型仍然只建议下一动作，Harness 负责在模型外部装配运行上下文、工具、策略、预算、审批、检查点、完成验证和观测事件。

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 区分 Agent Loop 的状态推进职责与 Harness 的运行时控制职责。
- 实现双重预算、工具白名单、人工审批暂停以及同一工具调用的恢复。
- 用不可变 `RunState`、检查点端口和脱敏事件构建可测试的执行轨迹。
- 用确定性完成检查约束停止条件，识别副作用工具的幂等与恢复边界。

## Java 对照

### 对照卡：Harness 与应用容器/工作流执行器 {#compare-harness-loop}

- 共同用途：在受控运行环境中重复决策、执行、验证和保存状态，直到满足停止条件。
- 可验证行为差异：Agent Loop 定义“动作—观察—下一动作”的状态推进；Harness 额外托管模型之外的工具、策略、预算、审批、持久化和观测控制面。
- Python 适用场景：长任务 Agent、代码 Agent、跨系统自动化以及需要人工审批和断点恢复的智能流程。
- Java 开发者常见误区：把 Harness 当成 Prompt 包装器，或者恢复时重新询问模型，导致动作漂移和副作用重复。
- 修正方式：在执行前持久化待处理 `call_id`，恢复同一动作；工具使用幂等键，最终答案还要通过确定性验收。

```java
while (state.isRunnable()) {
    Action action = state.pendingAction().orElseGet(() -> model.next(state));
    state = policy.authorize(action, state);
    state = executor.executeOrPause(action, state);
    checkpointStore.save(state);
}
```

```python
# Loop 推进状态；Harness 在每个边界保存快照并应用确定性策略。
while state.status == "running":
    action = state.pending_call or model.next_action(state.objective, state.history)
    state = harness.execute_or_pause(action, state)
    checkpoint_store.save(state)
```

## Python 知识

### Loop 契约

一个可运行的循环至少要明确六项内容：触发条件、任务目标、可进入模型的上下文、允许的动作、完成验证和停止预算。仅写“请持续工作直到完成”没有可验证的结束条件，也无法区分模型卡住、工具失败和任务真正完成。

本章把一次模型决策计为一个 `step`，把真正进入白名单工具处理器的尝试计为一次 `tool_call`。未知工具和人工拒绝会形成观察，但不会执行处理器；工具抛异常仍消耗调用预算。

### Harness 控制面

- `AgentModel`：供应商无关的概率决策端口。
- `ToolSpec`：工具处理器与是否需要审批的静态策略。
- `HarnessLimits`：模型轮数和工具调用次数预算。
- `RunState`：历史、待处理调用、状态、答案和错误组成的不可变快照。
- `CheckpointStore`：内存、数据库或持久工作流引擎的替换端口。
- `EventSink`：只记录动作类型、步骤和结果状态的脱敏观测端口。
- `CompletionVerifier`：由代码检查“是否真的完成”，而不是直接相信模型自报成功。

### 暂停、恢复与副作用

审批必须发生在工具执行之前。Harness 先把 `pending_call` 和稳定 `call_id` 写入检查点，再返回 `waiting_approval`；恢复时直接处理这个调用，不能重新请求模型生成动作。

检查点无法单独保证“恰好一次”。进程可能在外部系统已成功、但本地成功快照尚未保存时崩溃，因此付款、发布和外发消息等工具还必须把 `call_id` 传给下游作为幂等键。教学实现采用内存存储；生产实现还应考虑事务 outbox、租约、并发抢占、版本迁移和敏感数据清理。

### 教案：暂停之后，恢复哪一步（建议 40 分钟）

1. **场景导入（5 分钟）：** 模型要发布周报，发布必须人工批准。先写出 `running → waiting_approval → completed` 的路径，以及拒绝或预算耗尽时的终态。
2. **追踪检查点（10 分钟）：** 沿 `RunState.pending_call` 找到调用在执行前保存的位置。暂停后核对 `call_id`、`step`、`tool_calls`；解释审批前为何 `tool_calls` 仍为零。
3. **恢复实验（10 分钟）：** 分别运行批准与拒绝命令，记录事件顺序和发布记录数。拒绝后继续追踪完成验证，解释为什么本例最终由模型预算收敛，而不是立即返回完成。预测恢复时若重新询问模型而不使用 `pending_call`，可能导致动作改变或重复执行。
4. **失败窗口（5 分钟）：** 假设周报已发布，但保存成功检查点前进程崩溃。讨论为何 `call_id` 必须传到下游作为幂等键；内存检查点无法承担跨进程持久化。
5. **练习与自测（10 分钟）：** 给批准、拒绝、工具异常和完成验证失败各写一条状态轨迹，再实现 `_drive` 与 `_handle_call`。自测：审批通过是否等于任务完成？不等于；还需执行结果和 `CompletionVerifier`。

## 可运行示例

### 示例：ch18-harness

[ch18_harness.py](examples/ch18_harness.py) 是演示入口；[models.py](examples/harness_runtime/models.py)、[ports.py](examples/harness_runtime/ports.py)、[runtime.py](examples/harness_runtime/runtime.py) 和 [adapters.py](examples/harness_runtime/adapters.py) 组成一个小型 Harness 工程包。

离线 `ReportModel` 请求发布周报。发布结果用内存字典模拟，脚本不会向外部系统发送内容。首次运行在副作用前暂停；随后可选择批准或拒绝，观察同一个 `call_id` 如何恢复，以及是否真的产生发布记录。

在仓库根目录执行以下命令，按章节清单同时验证两条路径：

```bash
python -m tools.run_example --chapter 18
```

本章清单运行 `--decision both --trace`。两个场景各用全新的业务字典、检查点和事件列表，因此批准产生的记录不会进入拒绝场景。直接运行脚本且不带参数时，仍保留原来的批准流程和四行摘要输出。

#### 先批准：决策、执行、验证分别发生在哪一步

```bash
python chapters/18-agent-harness-loop/examples/ch18_harness.py --decision approve --trace
```

关键输出：

```text
paused=waiting_approval pending=publish-weekly-001
checkpoint step=1 tool_calls=0 published_count=0
completed=completed answer=周报已发布 tool_calls=1
published=本周完成 3 个任务
decision=approve steps=2 tool_calls=1 published_count=1 error=None
```

第 1 次模型决策只提出工具调用，因此暂停时工具次数和发布记录数都为零。批准后直接执行检查点里的调用，执行本身不再增加模型决策次数。成功观察进入历史，第 2 次模型决策才给出“周报已发布”；`verify_publication` 同时核对内存业务表里的正文和模型回答，验收通过后返回 `completed`。真实项目应把内存表查询替换为发布系统的权威结果查询。

#### 再拒绝：为什么没有副作用，却仍然耗尽模型预算

```bash
python chapters/18-agent-harness-loop/examples/ch18_harness.py --decision deny --trace
```

关键输出：

```text
checkpoint step=1 tool_calls=0 published_count=0
completed=failed answer=None tool_calls=0
published=<none>
decision=deny steps=3 tool_calls=0 published_count=0 error=model step budget exhausted
observation call_id=publish-weekly-001 tool=publish_report result=None error=approval denied
```

拒绝只阻止这次工具执行，并写入 `approval denied` 观察。`ReportModel` 随后回答“周报未发布”，但任务目标仍是“发布周报”，业务表中也没有发布记录，所以完成验证返回“周报尚未发布”。反馈进入历史后，固定的离线模型再次回答“周报未发布”，仍未通过验收。总计 3 次模型决策后，Harness 以 `failed` 结束。

这里的失败原因是模型决策预算耗尽，拒绝本身已经按预期生效。`answer=None` 表示没有验收通过的最终答案；工具观察仍留在历史里。本章没有 `cancelled` 状态，不能把这条路径解释成“拒绝后立刻成功结束”。脚本退出码为 0 则表示教学场景完整跑完，与业务任务的 `failed` 是不同层次。

#### 对照轨迹，而不是只看最后一句话

`--trace` 的 `step` 是累计模型决策次数，多个事件可以发生在同一步。`tool_result` 表示产生了一条观察，可能是拒绝反馈，并不必然意味着处理器执行过。结合 `tool_calls` 和业务表里的 `published_count` 才能确认副作用。

| 检查位置 | 批准路径 | 拒绝路径 |
| --- | --- | --- |
| 首次暂停 | `step=1`，工具 0 次，发布 0 条 | `step=1`，工具 0 次，发布 0 条 |
| 恢复后的工具观察 | `result=published`，无错误 | `result=None`，`error=approval denied` |
| 完成验证 | 第 2 步通过 | 第 2、3 步各反馈一次未发布 |
| 运行终态 | `completed`，工具 1 次，发布 1 条 | `failed`，工具 0 次，发布 0 条 |

阅读代码时依次跟踪 `_run_demo` 中的 `harness.start`、`harness.resume` 和 `verify_publication`，再进入 `_drive → _handle_call → _observe`。若直接在两次进程启动之间谈“恢复”，内存检查点已经不存在；本例演示的是同一进程内的暂停与继续。

## 练习

- `CH18-EX01`：[实现 Harness Loop](exercises/exercise_ch18.py)，完成 `_drive` 和 `_handle_call`，覆盖预算、审批、恢复、工具异常与完成验证。

建议先完成无审批工具的正常路径，再加入暂停恢复，最后处理双重预算和验收反馈。运行 `python -m tools.check_exercise --chapter 18`；完成后查看带设计注释的[参考答案](../../solutions/ch18_harness.py)。

## 验证方式

章节清单验证批准和拒绝两条路径的实际输出：批准最终为 `completed`、2 次决策、1 次工具执行和 1 条发布记录；拒绝最终为 `failed`、3 次决策、0 次工具执行和 0 条发布记录，并包含两次验收反馈及预算耗尽事件。两条路径的初始检查点都必须是 `step=1`、`tool_calls=0`、`published_count=0`。

练习验收还会验证恢复执行原 `call_id`、第二次工具执行被预算阻止，以及验收失败会返回循环继续修正。

运行 `python -m tools.check_exercise --chapter 18 --solution` 验证参考答案；运行 `python -m tools.run_example --all` 和 `python -m tools.check_exercise --all --solution` 验证全部 24 章。后续从[第 19 章](../19-model-sdk/README.md)进入真实 SDK、MCP 与持久化实战。

## 章节总结

Loop 是 Harness 的心跳，但不是全部。可靠性来自模型外部的确定性控制面：上下文边界、工具能力、预算、审批、检查点、幂等、完成验证和观测事件共同决定 Agent 在真实工程中能否安全地持续运行。
