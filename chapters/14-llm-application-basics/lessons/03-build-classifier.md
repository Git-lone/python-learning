# 第 3 课：从规则基线走到模型端口

> 本课约 45 分钟。请从仓库根目录运行命令，边看输出边读[示例源码](../examples/ch14_llm_basics.py)。本课**没有真实 LLM 调用**；离线替身用于教清接口、消息和返回值边界。

## 1. 先跑一个最简单的基线

打开 `RuleBasedModel.complete`，它的核心逻辑相当于：

```python
text = messages[-1].content.lower()
intent = "refund" if "refund" in text else "other"
```

第一行取最后一条消息的内容并转小写，第二行只找连续子串 `refund`。这段代码没有“理解否定句”，也没有“理解同义表达”。它的优点是便宜、稳定、结果可复现，所以适合当基线。真实 LLM 是否有价值，应和这样的基线在同一份样本上比较，而不是只看几条成功演示。

先猜四条消息的输出，再执行：

```powershell
python chapters/14-llm-application-basics/examples/ch14_llm_basics.py --cases
```

| 消息 | 人工期望 | 规则会给什么 | 观察点 |
|---|---|---|---|
| `Please refund order SO-1` | `refund` | `refund` | 显式关键词正例 |
| `I was charged twice. Can I get my money back?` | `refund` | `other` | 同义表达漏判 |
| `Please do not refund order SO-1` | `other` | `refund` | 否定句误判 |
| `Where is my invoice?` | `other` | `other` | 普通负例 |

如果你的输出与“规则会给什么”不同，检查实际执行的是哪个文件，以及是否从仓库根目录运行。表格里的“人工期望”只是本课为这四句设定的标签，不代表真实业务数据集。

## 2. 试着修规则，并观察新问题

在 `RuleBasedModel.complete` 中，临时把计算 `intent` 的一行替换为下面几行，再运行 `--cases`：

```python
# 先处理明确的否定，再识别两种退款表达；这是课堂上的临时规则。
if "do not refund" in text:
    intent = "other"
elif "refund" in text or "money back" in text:
    intent = "refund"
else:
    intent = "other"
```

四条教学样本现在可能全部通过。但新消息 `I do not want my money back` 会被判成什么？客户真正想要什么？这说明靠添加短语能修某个样本，也可能继续漏掉不同写法或否定关系。若业务表达范围很有限，规则仍可能是最佳方案；若表达持续变化，才值得在**同一批标注消息**上试 LLM。

完成这个小实验后恢复原代码。课程后续的输出与练习以原始关键词基线为准。

## 3. 为什么不把关键词规则写死在业务函数里

如果 `classify` 直接判断 `"refund" in user_text`，以后接入真实模型时就要改业务流程。我们先定义一个最小端口：

```python
class ModelClient(Protocol):
    def complete(self, messages: Sequence[Message]) -> str: ...
```

`Protocol` 描述调用方需要的行为：接收消息序列、返回字符串。实现者只要提供兼容的 `complete` 方法，`classify` 就能调用。与 Java 接口相似，但 Python 的类型提示主要服务静态检查和阅读；运行时仍要处理返回了坏数据的情况。

`Message` 是 `@dataclass(frozen=True, slots=True)`：课程用它保存 `role` 和 `content`。`frozen=True` 避免构造后意外修改，`slots=True` 让实例字段受限。`Role = Literal["system", "user", "assistant"]` 是类型提示，不应被当成网络输入的运行时校验器。

## 4. 沿调用链走一次

运行默认示例：

```powershell
python -m tools.run_example --chapter 14
```

你应看到 `intent=refund confidence=0.92`。按源码顺序追踪：

1. `main` 创建 `RuleBasedModel()`，传入 `Please refund order SO-1`。
2. `classify` 构造 `system` 消息，要求返回含 `intent` 与 `confidence` 的 JSON 对象；构造 `user` 消息，放入客户原文。
3. `model.complete(messages)` 调用离线替身。它只读取最后一条消息，按子串规则产生 JSON 字符串。
4. `json.loads(...)` 将字符串变成 Python 值；`isinstance(payload, dict)` 检查根节点是对象。
5. `main` 从字典取出两个字段并打印。

请在[学案](../STUDY_GUIDE.md)写下第 3 步的**原始字符串**与第 4 步的**Python 值**有何不同。提示：`json.loads` 能解析 `[]`、`42`、`null` 等合法 JSON；它们都不符合本业务要求的对象根节点。

## 5. 两个容易被忽略的代码事实

第一，示例里的 `confidence=0.92` 是替身硬编码的值。它没有统计含义，不能据此设置“超过 0.9 自动退款”。如果真实模型也自报一个数字，仍需用有标签数据验证它与正确率的关系。

第二，当前 `classify` 只检查根节点。`{}`、`{"intent": "banana"}` 都能通过这个检查；后者甚至会被打印成分类结果。示例是逐步教学的起点，不是满足了[第 2 课合同](02-stack-and-scenarios.md)的成品。下一课会把“能解析”和“可交给业务”拆开。

## 6. 动手改一个输入

把示例 `main` 中的消息临时改为 `Please do not refund order SO-1`，运行默认示例，预测输出。再改为 `I was charged twice. Can I get my money back?` 重跑。记录为什么两个结果与人工期望不一致，最后恢复原输入。

如果不想修改文件，前面的 `--cases` 命令能一次看到四条样本。无论哪种方式，都应能指出误判来自关键词规则，而非 `json.loads`。

**本课产物：** 一张四行样本表、完整调用链，以及对当前代码缺口的说明。下一课会处理不合合同的输出并给这张表加上评测结论。
