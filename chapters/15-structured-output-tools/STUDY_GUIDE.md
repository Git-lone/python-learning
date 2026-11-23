# 第 15 章学案：结构化输出与工具注册

配合[本章讲解](README.md)使用。完成后，你应能把一段模型建议送进应用，并指出它在哪一层被接受或拒绝。

## 1. 从“分类建议”走向“动作建议”

第 14 章把客户消息分类成 `refund` 或 `other`。即使分类正确，也只能说明客户可能要退款，不能直接调用退款接口。本章研究下一步：模型提出一个工具名称和参数时，应用如何决定是否执行。

工具调用是应用执行本地处理器；模型只负责提出建议。JSON 是表达建议的格式，并不是执行许可。本课先开放纯计算 `add`，避免订单接口、身份认证和网络故障掩盖分派边界。客服的订单查询、知识检索也会经历相似入口；真正接业务系统时还需要授权。

先看这条建议：

```json
{"name":"add","arguments":{"left":2,"right":3}}
```

应用需要回答三个问题：它是否符合调用请求的结构？`add` 是否在允许列表中？它的两个操作数是否满足工具参数合同？这三项通过后，才执行 `2 + 3`。

## 2. 与 Java 请求处理对应起来

| 本课对象 | Java 中的近似职责 | 证明什么 |
|---|---|---|
| `json.loads` | JSON 反序列化 | 文本能被解析；尚不能证明根节点是对象 |
| `parse_tool_call` | 请求 DTO 的运行时校验 | 顶层字段、工具名类型、参数对象符合入口合同 |
| `ToolRegistry.execute` | `Map<String, Handler>` 命令分派 | 应用显式注册了这个名字 |
| `add` 的整数检查 | 业务处理器参数校验 | `left`、`right` 是整数且不是布尔值 |
| 成功或拒绝观察 | 服务结果对象或错误响应 | 本次实际发生了什么，可供调用方记录 |

Python 中 `dict[str, object]`、`Mapping[str, object]` 是类型提示，不会替你检查或冻结运行时数据。`json.loads('[]')` 得到列表，`json.loads('null')` 得到 `None`；反序列化成功后还得判断结构。

本例刻意使用纯 JSON；第 14 章练习对完整代码围栏的兼容不自动延续到这里。若将来接入供应商 SDK，应先在适配层取得其结构化调用，再应用自己的合同检查。

## 3. 沿着真实代码找执行边界

打开[完整实践](examples/ch15_tool_contract.py)和[原注册表](examples/ch15_tools.py)，按以下顺序读：

1. `CASES` 保存固定的模型输出替身。它让输入可重复，不代表真实模型一定返回这些值。
2. `parse_tool_call` 解码 JSON，要求根节点为字典，顶层恰好包含 `name`、`arguments`；名称必须是非空白字符串，参数必须是字典。此时不做加法，也不猜测模型漏掉的参数。
3. `ToolRegistry.execute` 用名称查应用维护的字典。找不到就抛出 `UnknownToolError`（继承 `KeyError`），不会尝试同名函数、`eval` 或 shell。
4. `add` 读取两个参数，先校验再计算。`True` 在 Python 中是 `int` 的子类，因此必须显式排除；字符串 `"2"`、浮点数 `2.0` 也不能偷偷转成整数。
5. `run_suggestion` 把可预期错误转换成带 `stage` 的拒绝观察；只有正常返回才有 `result`。没有自动修参、重试、退款执行或后续模型调用。

这里的合同分两层：入口知道所有工具都有名称和参数对象；`add` 才知道参数需要整数。让注册表猜各个工具的参数，会把业务合同塞进分派逻辑，增加维护成本。

## 4. 先预测，再运行

先盖住“核对结果”列，自己判断每条输入的停止位置，然后在仓库根目录运行：

```powershell
python chapters/15-structured-output-tools/examples/ch15_tool_contract.py
```

| 案例 | 输入关键部分 | 核对结果 |
|---|---|---|
| `success` | `add`，`left=2`、`right=3` | `status=ok`，`result=5` |
| `bad-parameters` | `add`，`left=true`、`right=3` | `tool-parameters` 拒绝；已经进入 `add`，没有执行加法 |
| `unknown-tool` | `delete_order` | `allowlist` 拒绝；没有调用任何处理器 |
| `invalid-structure` | 根节点为 `[]` | `request-contract` 拒绝；还没到注册表 |
| `invalid-json` | `not-json` | `request-contract` 拒绝；JSON 解码失败 |
| `invalid-arguments` | `arguments=[2,3]` | `request-contract` 拒绝；参数不是对象 |

前三行应为：

```text
case=success {"status": "ok", "tool": "add", "result": 5}
case=bad-parameters {"status": "rejected", "stage": "tool-parameters", "reason": "left and right must be integers"}
case=unknown-tool {"status": "rejected", "stage": "allowlist", "reason": "unknown tool: delete_order"}
```

单独核对一个案例时，使用 `--case bad-parameters` 或 `--case unknown-tool`。错误建议被正确拒绝也是一次成功演示，因此脚本的退出码为 `0`；不要把进程成功退出误解成所有动作都获准执行。

最容易看错的是坏参数：本例的业务参数校验写在处理器内部，所以处理器被调用过，但计算尚未完成。若换成付款工具，参数、权限和业务检查必须放在实际扣款之前，不能先执行再判断返回值。

## 5. 动手完成并核对证据

先完成[注册表练习](exercises/exercise_ch15.py)，保持它只负责注册和分派：

```powershell
python -m tools.check_exercise --chapter 15
```

再运行新增实践的边界检查：

```powershell
python -m pytest tests/test_tool_contract.py -q
python -m tools.run_example --chapter 15
```

[实践检查](../../tests/test_tool_contract.py)在 `add` 外包了一层记录器：进入处理器记 `entered`，完成运算记 `completed`。检查坏参数只有 `entered`，未知工具和入口错误没有记录。这比只看到一段报错更能证明失败停止的位置。

自行向 `CASES` 加两条输入再运行：一条缺少 `arguments`，一条把 `left` 改成 `"2"`。先记录预测，再记录输出；应分别停在 `request-contract` 和 `tool-parameters`。不要通过补默认值或自动转整数让反例“成功”。

## 6. 本例能保证什么，还缺什么

- 允许列表只有 `add`，它没有外部 I/O，所以本次实践不会改订单或写数据库。“只读”来自实际注册的函数能力，注册表没有自动检查函数是否写数据。
- 入口严格限制顶层字段；现有 `add` 只检查两个必需整数，仍会忽略参数对象中的额外键。本例没有实现完整 JSON Schema、数值范围或输出大小限制。
- 已注册、参数合法不代表当前用户有业务权限，也不证明模型选择符合用户意图。订单查询需要用户身份和订单归属校验，退款还需要金额和审批等业务规则。
- 专用的 `UnknownToolError` 区分未注册名称与处理器内部的 `KeyError`。`ValueError` 则只按本例 `add` 的约定解释为参数失败；增加工具时应定义明确的参数异常，避免掩盖处理器内部缺陷。
- 这里仅把观察打印出来，没有将结果送回模型、做循环重试或持久化。后续 Agent 章节再讨论这些机制；MCP 协议在第 20 章介绍。

## 7. 课末自检

用自己的话回答：合法 JSON、符合入口合同、工具已注册、参数合法，分别排除了哪一种错误？为什么四项成立仍不足以允许退款？

本章交付是：注册表练习通过；六个案例输出与预测对得上；能够指出坏参数与未知工具的不同停止位置。完成后再对照带注释的[注册表参考答案](../../solutions/ch15_tools.py)。
