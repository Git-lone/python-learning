# 第 15 章：结构化输出与工具调用

**先修章节：** [第 4 章：面向对象与数据类](../04-oop-dataclasses/README.md)、[第 5 章：异常处理](../05-exceptions/README.md)、[第 8 章：类型提示](../08-type-hints/README.md)、[第 14 章：LLM 应用基础](../14-llm-application-basics/README.md)

工具调用不是让模型执行代码，而是让模型提出一个结构化动作，再由应用决定是否允许以及如何执行。

第 14 章拿到的是 `intent=refund` 这样的分类建议，并明确它不等于退款授权。本章继续研究：当建议变成 `{"name":"add","arguments":{"left":2,"right":3}}`，应用如何在执行前检查请求结构、允许列表和工具参数。先用没有外部 I/O 的加法走通这条链，再考虑真实订单查询。

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 把工具名称、说明、参数约束和执行函数建模为显式注册表。
- 严格区分“模型提出调用”和“应用授权执行”，拒绝未知名称与非法参数。
- 把工具结果和错误转换为可记录、可再次提供给模型的观察事件。

## Java 对照

### 对照卡：工具注册与命令分派 {#compare-tool-dispatch}

- 共同用途：把声明式命令路由到受控处理器，并统一记录结果。
- 可验证行为差异：模型只能生成候选工具调用；Python 应用仍负责白名单、参数解析、授权和真实副作用。
- Python 适用场景：查询订单、执行计算、搜索知识、创建工单和调用内部 API。
- Java 开发者常见误区：把模型输出直接交给 `eval`、shell 或反射调用任意函数。
- 修正方式：注册最小工具集合，逐字段校验参数，并为写操作增加幂等、权限和人工审批。

```java
Map<String, ToolHandler> tools = Map.of("add", this::add);
Object result = tools.get(call.name()).execute(call.arguments());
```

```python
# 模型只能选择注册表里的名字，不能指定任意 Python 函数。
registry.register("add", add)
result = registry.execute(call.name, call.arguments)
```

## Python 知识

工具描述面向模型，执行器面向应用。不要把数据库连接、访问令牌或内部对象交给模型；工具参数只包含完成动作所需的最小数据。参数校验必须发生在任何副作用之前。

工具失败不一定意味着整个 Agent 失败。可恢复错误可以转成观察，交给模型调整参数；权限拒绝、预算耗尽和高风险动作则应由确定性策略终止或请求人工确认。

### 教案：模型可提议，执行器要验证（建议 40 分钟）

1. **承接分类建议（5 分钟）：** 回看第 14 章的三道关。本章把分类数据换成动作建议，但合法结构仍不是业务授权。
2. **沿调用链读代码（10 分钟）：** 对照学案，依次找到 `parse_tool_call`、`ToolRegistry.execute`、`add`。分别解释它们证明了什么。
3. **预测并运行反例（15 分钟）：** 先猜布尔参数、未知名称和数组根节点在哪层停止，再运行新增实践核对输出。特别区分“进入处理器”和“完成计算”。
4. **练习与自测（10 分钟）：** 完成注册表练习。最后说明为什么只注册 `add` 能限制本例能力，却不能替真实订单查询做用户权限校验。

## 可运行示例

### 示例：ch15-tools

[ch15_tools.py](examples/ch15_tools.py) 注册一个经过整数校验的 `add` 工具，并执行固定结构化调用。运行：`python -m tools.run_example --chapter 15`。

### 示例：ch15-tool-contract

[ch15_tool_contract.py](examples/ch15_tool_contract.py) 复用上面的注册表和 `add`，补齐不可信 JSON 的入口合同与拒绝观察。无需 API Key，默认一次运行六个固定案例；它模拟模型返回的文本，没有调用真实模型，也没有实现模型循环。

在仓库根目录运行完整实践或单独一个反例：

```powershell
python chapters/15-structured-output-tools/examples/ch15_tool_contract.py
python chapters/15-structured-output-tools/examples/ch15_tool_contract.py --case bad-parameters
python chapters/15-structured-output-tools/examples/ch15_tool_contract.py --case unknown-tool
```

阅读[学案中的输入、预期与解释](STUDY_GUIDE.md)，先预测再运行。完整执行顺序是：

```text
模型建议文本 → JSON 解码与请求结构检查 → 注册表查找 → add 参数检查 → 加法结果
                       ↓ 拒绝                 ↓ 拒绝         ↓ 拒绝
               request-contract          allowlist     tool-parameters
```

## 练习

- `CH15-EX01`：[实现 ToolRegistry](exercises/exercise_ch15.py)，支持注册、执行，并拒绝空名称、重复名称和未知名称。

注册表只负责路由，不替处理器猜测参数。完成后运行 `python -m tools.check_exercise --chapter 15`，再查看带注释的[参考答案](../../solutions/ch15_tools.py)。

## 验证方式

示例应输出 `tool=add result=5` 和 `allowlist=enabled`。练习检查覆盖正常执行、未知工具、重复注册和空名称。

新增实践的六行输出中，`success` 得到 `result=5`；其余均为 `status=rejected`。布尔参数停在 `tool-parameters`，未知工具停在 `allowlist`，数组根节点、非法 JSON 和非对象参数停在 `request-contract`。错误案例被预期地拒绝，所以演示进程仍以 `0` 退出。

`python -m tools.run_example --chapter 15` 会校验两个示例的输出。还可单独运行本章实践的边界检查，确认拒绝时究竟有没有进入处理器：

```powershell
python -m pytest tests/test_tool_contract.py -q
```

## 章节总结

工具调用的安全性来自应用控制，不来自模型自律。白名单、参数校验、权限、幂等和审计共同构成 Agent 的动作边界。

本例只实现入口合同、允许列表和整数校验；只读边界来自应用只注册无外部 I/O 的 `add`。注册表不会自动识别写操作，已注册也不代表当前用户有业务权限。接真实订单查询前，还需检查用户身份与订单归属。
