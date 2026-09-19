# 第 21 章：LangGraph 持久化与人工审批

先修：第 7、11、18、20 章。第 18 章用手写循环讲原理，本章用真实 LangGraph 和 SQLite 验证跨进程恢复，不重新造一个工作流引擎。

## 学习目标

- 长任务暂停后跨进程恢复并避免重复副作用。
- 先审批，后副作用；幂等键与请求内容绑定。
- 完成“带载荷冲突校验的幂等发布”并解释失败测试的意义。

## Java 对照

### LangGraph 持久化与人工审批 {#compare-durable-workflow}

- 共同用途：长任务暂停后跨进程恢复并避免重复副作用。
- 可验证行为差异：LangGraph 的 interrupt 恢复会重新执行所在节点，并非恢复 Python 栈帧。
- Python 适用场景：需人工确认的 Agent 操作和可恢复工作流。
- Java 开发者常见误区：把 checkpoint 等同于业务事务的 exactly-once。
- 修正方式：先审批，后副作用；幂等键与请求内容绑定。



可以类比持久化状态机加业务幂等表，而不是可序列化的线程栈。`interrupt` 后恢复会从所在节点开头重新执行；节点内已经做过的副作用可能再次发生。

## Python 知识

### 一条完整链路

`START -> approve(interrupt) -> publish -> END`

看 [durable.py](../../agent_lab/durable.py)：`State` 保存请求和草稿；`SqliteSaver` 保存图状态；`thread_id` 找到同一会话；`Ledger` 记录合成发布结果。审批前没有发布操作。恢复参数必须是真正的布尔值，字符串 `"false"` 不能当作审批通过。

## 可运行示例

### 运行记录：ch21-demo

```powershell
python -m tools.run_example --chapter 21
python -m pytest tests/test_durable.py -q
```

例子分别用两个独立 Python 进程运行 start 和 approve，第一个进程退出后仍能恢复。输出先是 `waiting_approval`、`deliveries=0`，再是 `published:demo-thread`、`deliveries=1`，临时数据库随后自动清理。

手动观察持久化文件：

```powershell
python -m agent_lab.durable start --directory .local/demo --thread demo-1
python -m agent_lab.durable reject --directory .local/demo --thread demo-1
```

用新 thread 再走 approve 路径；已存在 thread 不能覆盖启动，无待审批状态不能继续审批。

### 为什么仍然要幂等

设发布已写入业务库，进程却在写下一条 checkpoint 之前退出。恢复后框架可能再次执行发布。因此业务库使用唯一 `request_id`，将同一个 key 与相同 body 绑定；重复相同载荷得到同一结果，不同载荷必须报错。

本章同一个业务事务保护幂等表，不保证“外部邮件也恰好发送一次”。真实跨系统副作用需要下游幂等键或 outbox 等机制；并发恢复同一个 thread 还要加单写者约束或租约，不能仅靠 SQLite 文件。

## 练习

实现 [publish_once](exercises/exercise_ch21.py)：创建表、参数化 INSERT、按 key 去重、检查载荷冲突、关闭连接。返回 `published:<request_id>`。

```powershell
python -m tools.check_exercise --chapter 21
python -m tools.check_exercise --chapter 21 --solution
```

[参考答案](../../solutions/ch21_durable_workflow.py)。测试同时覆盖接受、拒绝、重新打开数据库、重复调用和并发重复请求。

### 面试追问

审批接口如何防越权？当前只有本地教学 CLI，生产服务必须将 thread 归属、操作者身份、待审批动作和载荷摘要绑定，并审计审批结果。`thread_id` 是索引，不是凭证。

框架为什么值得引入？这里需要持久化、暂停恢复和状态检查；只有两个固定无状态 HTTP 调用时，普通函数组合可能更合适。

依据：[LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)、[持久化文档](https://docs.langchain.com/oss/python/langgraph/persistence)。SQLite 是本地学习方案，不是本课程已验证的分布式生产部署。

## 验证方式

运行 `python -m tools.check_exercise --chapter 21` 验证自己的实现，`--solution` 用于核对参考答案。示例合同由 `python -m tools.run_example --chapter 21` 验证；工程异常测试见根目录 tests。

## 章节总结

先审批，后副作用；幂等键与请求内容绑定。面试时同时说明实现、测试证据和未实现边界；公开原帖与自编练习分别见 [真实面经](../../career/INTERVIEW_EXPERIENCES.md) 和 [面试练习](../../career/INTERVIEW_PRACTICE.md)。
