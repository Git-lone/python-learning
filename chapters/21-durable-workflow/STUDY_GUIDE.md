# 第 21 章学案：持久化、审批与幂等

配合[本章讲解](README.md)使用。建议预留 50～60 分钟，在项目根目录用 PowerShell 完成。全程只运行本地 Python、LangGraph 和 SQLite，不需要 API Key，也不会发布真实消息。

## 本次要完成的任务

一条回复草稿已经生成，业务要求人工同意后才能发布。提交草稿的进程会退出，审批可能由之后启动的另一个进程完成。你要证明三件事：暂停时确实没有发布；进程退出后仍能找到原任务；人工拒绝后也能结束流程，但不留下发布记录。

本章的“发布”是写入本地账本，草稿固定为 `Synthetic reply`。它延续[第 18 章 Harness](../18-agent-harness-loop/README.md)的“先保存待执行动作，再等待审批”原则，但没有把第 18 章的模型、工具循环自动迁入 LangGraph。

| 要解决的问题 | 第 18 章 | 本章 |
|---|---|---|
| 保存什么 | `RunState` 与 `pending_call` | 图状态中的请求、草稿、审批结果与下一节点 |
| 保存在哪里 | 内存 `CheckpointStore` | 磁盘 `SqliteSaver` |
| 恢复哪个任务 | 原 `run_id` 与 `call_id` | 同一数据库中的 `thread_id` |
| 谁防止重复副作用 | 工具和下游需要支持幂等 | `Ledger` 的唯一请求键与正文校验 |

本章 CLI 为了简化演示，让 `request_id` 等于 `--thread`。概念上，`thread_id` 是流程索引，`request_id` 是业务幂等键；真实流程可能包含多个业务动作，不能据此认为二者永远相同，更不能把任一个 ID 当作审批凭证。

## 实验前先预测

先不运行，填写两列预测，把“实际观察”留到运行后。后续会在同一个全新目录中依次批准一条任务、拒绝另一条任务。

| 操作后 | 预测流程状态 | 预测整个账本的记录数 | 实际观察 |
|---|---|---|---|
| 启动 `approve-demo` | ________ | ________ | ________ |
| 批准 `approve-demo` | ________ | ________ | ________ |
| 启动 `reject-demo` | ________ | ________ | ________ |
| 拒绝 `reject-demo` | ________ | ________ | ________ |

为什么“拒绝后没有发布”不一定意味着整个账本的记录数是 0？先写下你的解释：________。

## 实验一：让暂停状态留在磁盘上

### 1. 准备独立的实验目录

确认已完成[项目安装](../../README.md)。以下命令直接使用项目虚拟环境，不依赖 PowerShell 激活脚本。

```powershell
# 在教程仓库根目录执行以下命令。
$py = ".\.venv\Scripts\python.exe"
$env:PYTHONUTF8 = "1"
$lab = Join-Path (Get-Location) (".local\ch21-" + (Get-Date -Format "yyyyMMdd-HHmmss-fff"))
$lab
```

记下打印的绝对路径：________。只在开始一轮新实验时重新生成 `$lab`；同一轮的启动、观察和审批必须使用原目录。目录保留在 `.local`，方便之后继续观察；它被 Git 忽略。

现有 `python -m tools.run_example --chapter 21` 是自动冒烟演示，会在完成后清理临时目录。因此本次手动实验直接调用相同的业务入口，不用那次演示生成的数据库。

### 2. 启动第一条任务

```powershell
& $py -m agent_lab.durable start --directory $lab --thread approve-demo
```

预期输出：

```text
waiting_approval
deliveries=0
```

命令此时已退出，终端重新出现提示符。没有 Python 进程留在这里等待你输入 `yes`；“等待审批”已经成为磁盘上的流程状态。

### 3. 用 inspect 观察已有任务

`inspect` 只读已有数据库，不执行图，不批准或发布；目录或数据库不存在时会报错，不会替你创建空库。

```powershell
& $py -m agent_lab.durable inspect --directory $lab --thread approve-demo
```

预期输出：

```text
checkpoint_found=True
request_id=approve-demo
approved=None
result=None
deliveries_total=0
deliveries_for_request=0
```

`approved=None` 表示状态里尚未出现审批结果，不是审批已返回空值。此时能找到检查点，却没有业务发布记录，说明 **保存流程进度与完成业务写入是两件事**。观察命令分别读取两个数据库，不承诺并发执行时的跨库一致性；本实验按顺序操作。

## 实验二：用另一个进程恢复同一任务

### 1. 批准，并重新观察

```powershell
& $py -m agent_lab.durable approve --directory $lab --thread approve-demo
& $py -m agent_lab.durable inspect --directory $lab --thread approve-demo
```

第一条命令会输出：

```text
published:approve-demo
deliveries=1
```

观察命令随后输出：

```text
checkpoint_found=True
request_id=approve-demo
approved=True
result=published:approve-demo
deliveries_total=1
deliveries_for_request=1
```

每次 `& $py ...` 都启动一个独立 Python 进程，即使它们共用一个终端。第二个进程没有第一个进程的内存；恢复成功依靠的是同一个目录中的检查点和相同的 `approve-demo` 标识。

也可以在首次暂停后关闭终端，再打开新终端。回到仓库根目录，重新设置 `$py`，把 `$lab` **直接赋值为你记录的原绝对路径**，再执行批准命令；不要重跑生成新目录的那一行。

### 2. 为什么重新运行的是节点，不是上一行代码

沿[实现](../../agent_lab/durable.py)阅读 `build_graph`：

1. 首次 `graph.invoke` 输入请求和草稿，`approve` 在 `interrupt(...)` 处暂停。
2. CLI 把 `--thread` 放入 `configurable.thread_id`，用它查找原状态。
3. `Command(resume=True)` 恢复原图；`approve` 从节点开头重进，这一次 `interrupt` 返回审批值。
4. `approved=True` 合并进状态，`publish` 才调用 `ledger.publish`，随后到达 `END`。

所以 `interrupt` 之前不能放未经保护的发送邮件、付款等操作。Java 开发者可以把它理解为持久化状态机重新执行一段节点代码，而非反序列化出一个继续运行的线程栈。

### 3. 改错一次标识，观察区别

```powershell
& $py -m agent_lab.durable approve --directory $lab --thread missing-demo
$LASTEXITCODE
& $py -m agent_lab.durable inspect --directory $lab --thread missing-demo
```

批准命令应报 `thread has no pending approval`，退出码为 `2`；观察中 `checkpoint_found=False`、`request_id=None`，全库仍是 `1`。当前请求发布数为 `None`：没有检查点就无法确定对应的业务键，不能将未知当成零条发布，更不能把“找不到任务”当成“任务已经结束”。

再审批一次已完成的任务：

```powershell
& $py -m agent_lab.durable approve --directory $lab --thread approve-demo
$LASTEXITCODE
```

同样应报“没有待审批”，退出码为 `2`。这验证的是 **CLI 防止再次审批**，不是业务层的重复发布去重；后者在实验四单独验证。

## 实验三：拒绝是一个终态，不是发布失败

在同一个目录使用另一条 thread，逐步运行：

```powershell
& $py -m agent_lab.durable start --directory $lab --thread reject-demo
& $py -m agent_lab.durable inspect --directory $lab --thread reject-demo
& $py -m agent_lab.durable reject --directory $lab --thread reject-demo
& $py -m agent_lab.durable inspect --directory $lab --thread reject-demo
```

启动时输出 `waiting_approval`、`deliveries=1`。暂停观察中 `request_id=reject-demo`、`approved=None`，当前请求发布数为 `0`。账本总数为 `1`，是因为上一条批准任务的记录仍在。

拒绝命令输出：

```text
rejected
deliveries=1
```

最终观察：

```text
checkpoint_found=True
request_id=reject-demo
approved=False
result=rejected
deliveries_total=1
deliveries_for_request=0
```

拒绝结果保存在检查点里，便于知道该流程如何结束；`Ledger` 中没有 `reject-demo` 的发布记录。虽然图仍经过名为 `publish` 的节点，但该节点的拒绝分支只返回 `rejected`，不会调用真正写账本的方法。

回填课前预测。全库发布数依次应是 `0 → 1 → 1 → 1`，两条任务结束后均能找到检查点，但只有批准任务有业务发布记录。

## 实验四：检查点之外，为什么还需要业务幂等

设想“账本写入已提交，下一条成功检查点尚未保存”时进程退出。恢复可能再次执行发布节点，单靠审批通过或检查点存在都不能防止重复副作用。

运行已有的[业务重放测试](../../tests/test_durable.py)，把幂等验证与 CLI 状态校验分开：

```powershell
& $py -m pytest tests/test_durable.py::test_replayed_business_operation_is_idempotent_and_payload_bound -q
```

预期为 `1 passed`。打开该测试，找出：8 次并发相同请求都返回相同结果；账本只有 1 条记录；更换正文后抛出载荷冲突；原记录数仍为 1。测试使用自己的临时目录，不改动你的 `$lab`。这里验证的是本地业务方法重放，没有模拟真实崩溃，也没有并发恢复同一个图。

唯一键防止插入第二条相同请求记录，载荷比较防止把“同一个 key、不同正文”误判为合法重试。checkpoint 和 ledger 位于不同文件、不同事务中；本实验说明本地业务写入可重放，不证明真实邮件或第三方 API 恰好调用一次。

## 常见卡点与下一步练习

| 现象 | 先检查什么 |
|---|---|
| `No module named langgraph` | 是否用项目 `.venv` 的 Python，是否已安装锁定依赖 |
| `thread already exists` | 是否对同一目录、同一 thread 再次执行 `start`；已有暂停任务应恢复，新实验才换 thread 或目录 |
| `thread has no pending approval` | 目录和 thread 是否与启动时一致；是否已经批准或拒绝 |
| 拒绝后仍显示 `deliveries=1` | 它是整个账本的总数；看 `deliveries_for_request` 才能判断本条任务有没有发布 |
| 关掉终端后 `$lab` 丢失 | 重新把变量设为记录的原路径；磁盘上的数据库仍然存在 |

现在完成[练习](exercises/exercise_ch21.py)中的 `publish_once`，实现参数化 SQL、唯一键去重、载荷冲突检查和连接关闭。先写自己的实现，再运行：

```powershell
& $py -m tools.check_exercise --chapter 21
```

模板初始抛出 `NotImplementedError` 是待完成题目。首次失败原因记录：________；修改后同一个 key、不同 body 的表现：________。需要核对时再读[参考答案](../../solutions/ch21_durable_workflow.py)，用 `--solution` 验证答案不会替你完成练习。

最后执行自动回归：

```powershell
& $py -m tools.run_example --chapter 21
& $py -m pytest tests/test_durable.py -q
```

它们分别检查原有两进程演示和持久化相关测试。测试覆盖批准/拒绝、重开连接、业务重复请求及非布尔审批值；不等于验证多 worker 同时恢复同一 thread，或验证任意时刻强制杀进程后的恢复。

## 过关自检

先独立回答，再展开核对。不要只凭命令退出码为 0 判断自己完成了实验。

1. 首次命令已经退出，为什么还能审批？必须保持哪两个定位条件？
2. 检查点存在，能否证明已经发布？哪两个输出能证明拒绝任务没有发布？
3. 恢复后是否从 `interrupt` 的下一行直接继续？把副作用放在它前面有什么后果？
4. 重复 `approve` 被拒绝，能否单独证明 `Ledger.publish` 幂等？
5. “同 key、同正文”和“同 key、不同正文”应分别怎样处理？
6. 这套 SQLite 实验尚未解决哪些真实服务问题？

<details>
<summary>自检要点</summary>

1. 状态已经写入 SQLite；要使用原数据库目录与相同 thread 标识。
2. 不能。拒绝任务应有 `result=rejected`，同时 `deliveries_for_request=0`；全库总数可以非零。
3. 恢复会重进所在节点，`interrupt` 再取得恢复值；它之前的副作用可能重复执行。
4. 不能。CLI 的状态校验与业务账本的幂等是两个边界，需要分别验证。
5. 前者复用已有结果且不新增记录；后者报载荷冲突且不覆盖原记录。
6. 未实现真实审批身份和授权、多 worker 单写者协调、跨系统事务、状态版本迁移，以及真实崩溃注入验证。

</details>

## 从本章带走什么

持久化工作流适合等待人工处理的报告发布、资料复核等长任务。若只是两步无状态查询，普通函数组合通常已经足够，不必为了使用框架而增加图和检查点。这里的 LangGraph、`SqliteSaver`、`interrupt` 与业务 `Ledger` 分别提供流程编排、状态存储、暂停恢复和副作用去重。

接下来[第 22 章](../22-retrieval-evaluation/README.md)学习如何评估检索证据质量，第 23 章将问答能力暴露为 API。这两步不会自动为本章增加审批接口或生产授权；迁移时仍要把调用者身份、流程归属、待批准动作和业务幂等键明确连接起来。
