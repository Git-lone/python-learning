# 第 14 章：从一条退款消息认识 LLM 应用

客服收到“我被扣了两次款，能退一笔吗？”之后，系统要决定这条消息该进入退款队列，还是继续由普通客服处理。关键词规则容易写，但“退款”“退钱”“扣重了”表达不同；`不要退款，我只是问进度`又包含“退款”两个字。我们用这个小问题学习 LLM 应用的完整链条：理解模型能力，选择合适的技术，接入模型边界，验证输出，再用反例检查效果。

**读者：** 已有 Java 后端经验，学过本教程第 4、5、8、13 章。**预计用时：** 约 2 小时，可分四次完成。**运行条件：** Python 3.12/3.13；正文和示例均可离线学习，不需要 API Key。

## 学习目标

- 用自己的话解释 token、下一 token 预测、消息、上下文窗口，以及它们为什么影响后端实现。
- 根据业务任务判断何时用规则、LLM、RAG 或 Agent，并画出本章分类服务的数据流。
- 读懂 `Message`、`ModelClient`、`RuleBasedModel` 和 `classify`，运行示例并指出两个规则误判。
- 区分 JSON 语法正确、字段合同有效和分类业务正确，完成解析练习。

## Java 对照

### 对照卡：模型客户端端口 {#compare-llm-boundary}

- 共同用途：通过稳定接口调用外部能力，再把结果转换为业务对象。
- 可验证行为差异：LLM 返回生成内容；“请返回 JSON”是一条指令，不等于 Java DTO 的编译期类型保证。
- Python 适用场景：开放文本的分类、抽取、总结、问答，以及后续 Agent 的决策输入。
- Java 开发者常见误区：让供应商 SDK 的响应类渗透业务层，或把模型文本直接交给退款接口。
- 修正方式：定义自己的 `ModelClient` 协议；把解析、字段校验、业务决策留在应用边界。

```java
interface ModelClient {
    String complete(List<Message> messages);
}
```

```python
class ModelClient(Protocol):
    def complete(self, messages: Sequence[Message]) -> str: ...
```

## Python 知识

本章是一组连续的课，不要求先记住一张技术名词表。每节末尾都有一个可以检查的产物，后面的课会使用前面的产物。建议按顺序学习，边读边填[学案](STUDY_GUIDE.md)。

| 课次 | 从哪个问题开始 | 完成后得到什么 |
|---|---|---|
| [第 1 课：LLM 在做什么](lessons/01-what-is-llm.md) | 同一句退款诉求为什么不能只查关键词？ | 能解释生成过程、消息和能力边界 |
| [第 2 课：技术栈与场景选择](lessons/02-stack-and-scenarios.md) | “接入 LLM”究竟要写哪些后端部件？ | 一份退款分流器的输入输出合同与架构图 |
| [第 3 课：从规则基线走到模型端口](lessons/03-build-classifier.md) | 怎样让代码可运行、可替换、可观察？ | 运行示例，记录两个反例及原因 |
| [第 4 课：输出校验与小型评测](lessons/04-validate-and-evaluate.md) | JSON 能解析就意味着分流正确吗？ | 完成练习，写出接受与拒绝的判据 |

先做一个预测：输入 `Please do not refund order SO-1` 时，本章离线替身会返回什么？写在学案中，学完第 3 课再核对。

## 可运行示例

### 示例：ch14-llm-basics

[ch14_llm_basics.py](examples/ch14_llm_basics.py) 是本章的可运行代码。它用 `RuleBasedModel` 模拟模型调用，保证没有网络和费用；它**不是**真正的 LLM。先运行默认示例，再运行四条对照消息：

```powershell
python -m tools.run_example --chapter 14
python chapters/14-llm-application-basics/examples/ch14_llm_basics.py --cases
```

第二条命令会暴露规则基线的漏判和误判。第 3 课会带你逐段读这份代码；真实 SDK 接入放在[第 19 章](../19-model-sdk/README.md)。

## 练习

完成 `CH14-EX01`：[parse_model_object](exercises/exercise_ch14.py)。它要接受纯 JSON 或完整的 `json` 代码围栏，拒绝坏 JSON、数组根节点和缺失字段。第 4 课给出逐步提示与检查办法；先独立写，再看[参考答案](../../solutions/ch14_llm_basics.py)。

## 验证方式

从仓库根目录执行：

```powershell
python -m tools.check_exercise --chapter 14
```

通过代码检查后，按[第 4 课](lessons/04-validate-and-evaluate.md)的四条小测口头解释：`0.92` 为什么不是可信概率、为什么 JSON 对象仍可能被拒绝、为什么 `do not refund` 会误判、为什么分类结果不能直接触发退款。

## 章节总结

本章产物是一个**可离线运行的分类应用骨架**，以及一份记录其不足的评测表。LLM 可以处理开放语言，应用必须控制输入、校验输出并决定业务动作。下一章深入[结构化输出与工具调用](../15-structured-output-tools/README.md)，第 16 章再加入外部知识，第 17、18 章讨论 Agent 与 Harness Loop。
