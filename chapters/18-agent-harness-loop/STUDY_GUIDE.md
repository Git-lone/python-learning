# 第 18 章学案：Harness、审批与恢复

配合[本章讲解](README.md)使用。先写状态表，再观察检查点与事件。

## Harness 是什么

Agent Loop 负责反复决策与观察；Harness 是托管这个循环的确定性运行环境，统一管理工具、权限、预算、审批、检查点、完成验证和事件。模型仍只是提出动作，不能自行修改运行规则。Java 开发者可以把它类比为工作流执行器加策略控制层，但其中的下一动作可能来自概率模型。

## 技术组成与落地场景

本章的包分为 `models.py`（状态和事件）、`ports.py`（模型/工具/存储接口）、`runtime.py`（循环控制）和 `adapters.py`（内存实现）。要发布报告、发消息或调用多工具的长任务，可能需要人工审批和恢复；只做一次无副作用分类时则无需完整 Harness。

运行预算至少覆盖模型轮数和工具次数；生产环境还常要限制总时间与费用。事件记录动作类型和结果，敏感参数不应默认落日志。`CompletionVerifier` 用业务证据决定是否真的完成，而不是只相信模型的最终文本。

## 代码怎样工作

[运行时](examples/harness_runtime/runtime.py)在模型提出工具调用后先保存 `pending_call`，需要审批就返回 `waiting_approval`。恢复时处理同一调用 ID，成功或拒绝都生成观察，最终答案还要经过验证。[示例](examples/ch18_harness.py)用内存存储展示全过程。内存检查点不能跨进程恢复；即使换成数据库，外部副作用仍需下游用 `call_id` 做幂等，避免“执行成功但保存检查点失败”后的重复操作。

## 课前热身

- 第 17 章的最小循环有哪些保护？哪些运行状态尚未持久化？
- 付款或发布需要人工审批时，审批应放在执行前还是执行后？

## 探究任务

1. 阅读[示例入口](examples/ch18_harness.py)与[运行时](examples/harness_runtime/runtime.py)，填写状态表：启动后 `status` ________、`pending_call` ________、`tool_calls` ________；批准后分别为 ________。
2. 运行 `python -m tools.run_example --chapter 18`，记录 `approval_requested` 与 `run_completed` 的顺序：________。
3. 假设发布成功、保存下一条检查点前崩溃。恢复时为何可能重复调用？`call_id` 应由哪一层用于幂等？________。

## 动手完成

- 完成[练习](exercises/exercise_ch18.py)的 `_drive` 和 `_handle_call`：正常工具、审批暂停、批准/拒绝、预算、完成验证依次实现。
- 运行 `python -m tools.check_exercise --chapter 18`。画出一次拒绝审批的轨迹与工具执行次数：________。

## 过关自检

- 能解释恢复时先处理 `pending_call` 而不是再次询问模型。
- 能区分模型步数和实际工具执行次数。
- 能说明检查点、幂等和完成验证各解决哪种失败。完成后再看[参考答案](../../solutions/ch18_harness.py)。
