# 第 21 章学案：持久化、审批与幂等

配合[本章讲解](README.md)使用，用两个进程验证同一会话能恢复。

## 持久化工作流是什么

短程序失败后可以重跑；带人工审批的长任务可能等待数小时，必须把状态保存下来。持久化工作流把当前节点、业务状态和待处理动作写成检查点，用会话 ID 找到它，再在下一次进程运行中恢复。恢复不等于把 Python 调用栈原样序列化；某些节点代码会重新执行，所以副作用需要幂等保护。

## 技术栈与落地场景

本项目用锁定版本的 LangGraph、`SqliteSaver`、`interrupt`、`thread_id` 与业务 `Ledger`。适用于报告发布审批、资料补充、人工复核和长时间任务。SQLite 只用于本地教学；跨机器多 worker 运行还要解决共享存储、并发恢复、租约和状态版本升级。[暂停恢复说明](https://docs.langchain.com/oss/python/langgraph/interrupts)。

审批和幂等承担不同职责：审批决定某个动作可否执行，幂等避免相同动作因重试而重复产生业务结果。`thread_id` 仅定位会话，不能代替操作者身份；业务 `request_id` 与请求内容绑定，相同载荷重试可返回既有结果，不同载荷必须拒绝。

## 代码怎样工作

[工作流](../../agent_lab/durable.py)按 `START → approve → publish → END` 推进。`approve` 中 `interrupt` 暂停，checkpointer 保存状态；另一个进程按同一 `thread_id` 提交审批后继续。`publish` 通过 Ledger 的唯一键处理重复调用。[练习](exercises/exercise_ch21.py)实现同一事务内的去重与载荷冲突检查；它不能保证外部邮件或第三方 API 也恰好执行一次。

## 课前热身

- 第 18 章内存检查点为何不能在进程退出后恢复？
- `thread_id` 是会话索引还是授权凭证？

## 探究任务

1. 阅读[持久化流程](../../agent_lab/durable.py)，填写 `START → ________ → ________ → END`，标出 `interrupt` 和真正发布的位置。
2. 运行 `python -m tools.run_example --chapter 21`，记录两个进程中先后出现的状态和 `deliveries`：________。
3. 推演“已写业务库、未写下一条 checkpoint”的崩溃窗口。同一个 `request_id`、相同 body 重试与不同 body 重试分别应怎样处理：________。

## 动手完成

- 完成[练习](exercises/exercise_ch21.py)的 `publish_once`，用参数化 SQL、唯一 key 和载荷冲突校验。
- 运行 `python -m tools.check_exercise --chapter 21`。记录重开数据库后重复请求的结果：________。

## 过关自检

- 能说出 SqliteSaver、`thread_id` 和 Ledger 各承担什么职责。
- 能解释审批拒绝、重复发布与载荷冲突三种不同终态。
- 能指出本地 SQLite 示例尚未验证多 worker 竞争。完成后再看[参考答案](../../solutions/ch21_durable_workflow.py)。
