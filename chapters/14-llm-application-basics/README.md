# 第 14 章：LLM 应用基础

**先修章节：** [第 4 章：面向对象与数据类](../04-oop-dataclasses/README.md)、[第 5 章：异常处理](../05-exceptions/README.md)、[第 8 章：类型提示](../08-type-hints/README.md)、[第 13 章：HTTP API 与可靠性](../13-http-api-resilience/README.md)

本章不绑定具体模型厂商。你将模型视为一个“接收消息、返回不可信文本”的端口，用确定性代码包住它。

## 学习目标

- 使用角色消息表达系统约束、用户请求和模型回复，并控制上下文长度。
- 用 `Protocol` 隔离模型客户端，使业务逻辑可替换、可离线测试。
- 解析和验证模型结构化输出，区分传输、模型拒绝、格式和业务校验错误。

## Java 对照

### 对照卡：模型客户端端口 {#compare-llm-boundary}

- 共同用途：通过稳定接口调用外部能力，并把返回值转换为领域结果。
- 可验证行为差异：LLM 返回概率文本，同一提示可能产生不同表述；提示中的“请返回 JSON”不是类型保证。
- Python 适用场景：分类、抽取、总结、对话、代码生成和 Agent 下一步决策。
- Java 开发者常见误区：把供应商响应类传遍业务层，或认为模型回复天然满足 DTO 契约。
- 修正方式：定义自己的 Message 与 ModelClient，集中处理请求、响应、解析、指标和错误映射。

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

系统消息描述长期约束，用户消息携带当前请求，助手消息保存先前输出。应用应保留完成任务所需的最小上下文；上下文越长不一定越准确，还会增加成本、延迟和提示注入面。

模型输出必须经过确定性检查。生产适配器还要记录模型名、请求标识、延迟、用量和结束原因，但不应默认记录完整敏感内容。测试使用 Fake/RuleBasedModel，比真实网络调用更快、更稳定。

## 可运行示例

### 示例：ch14-llm-basics

[ch14_llm_basics.py](examples/ch14_llm_basics.py) 定义供应商无关协议，用离线模型完成退款意图分类，并校验 JSON 对象。运行：`python -m tools.run_example --chapter 14`。

## 练习

- `CH14-EX01`：[实现 parse_model_object](exercises/exercise_ch14.py)，接受纯 JSON 或 Markdown JSON 围栏并检查必填字段。

不要用正则表达式“修复”任意坏 JSON。完成后运行 `python -m tools.check_exercise --chapter 14`，再查看[参考答案](../../solutions/ch14_llm_basics.py)。

## 验证方式

示例应输出 `intent=refund confidence=0.92`。练习检查覆盖纯对象、代码围栏、语法错误、数组根节点和字段缺失。

## 章节总结

LLM 是一个不确定的外部依赖，而不是新的业务层。用自己的协议隔离供应商，用确定性解析和校验把概率输出变成可靠输入。
