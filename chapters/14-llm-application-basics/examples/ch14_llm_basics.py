"""用协议隔离模型供应商，并把模型文本视作不可信输入。

阅读顺序：Message 定义消息结构，ModelClient 定义业务需要的能力，
RuleBasedModel 提供离线替身，classify 负责组装请求与解析响应。
这是应用调用边界的演示，不包含模型训练或真正的语言模型推理。
"""

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

Role = Literal["system", "user", "assistant"]
# Literal 供类型检查器提示合法角色，运行时不会自动拒绝其他字符串。


@dataclass(frozen=True, slots=True)
class Message:
    """一条对话消息，类似 Java record；冻结字段以减少调用过程中被改写的机会。"""

    role: Role
    content: str


class ModelClient(Protocol):
    """类似 Java 接口，但使用结构化匹配，实现类不必显式声明 implements。"""

    def complete(self, messages: Sequence[Message]) -> str:
        """接收有序消息并返回原始文本；JSON 解析属于调用方，不由端口承诺。"""

        ...


class RuleBasedModel:
    """用确定性关键词规则代替外部 SDK，让学习者先观察输入输出合同。"""

    def complete(self, messages: Sequence[Message]) -> str:
        """读取最后一条消息并返回分类 JSON；本示例约定调用方传入非空消息序列。"""

        # 离线替身保持模型端口真实，同时让测试结果完全确定。
        text = messages[-1].content.lower()
        # 这里是关键词规则，0.92 也是固定样例值，不代表真实模型置信度或效果。
        intent = "refund" if "refund" in text else "other"
        return json.dumps({"intent": intent, "confidence": 0.92})


def classify(model: ModelClient, user_text: str) -> dict[str, object]:
    """把用户文本转为分类对象；非法 JSON 或非对象响应直接报错。

    返回 dict 只说明解析成功，不说明 intent 正确，也不说明 confidence 可信。
    更换真实模型时可以保留业务函数，另写适配器实现 ModelClient。
    """

    # 业务层只依赖自己的协议，不感知任何供应商 SDK 类型。
    messages = [
        Message("system", "Return one JSON object with intent and confidence."),
        Message("user", user_text),
    ]
    # 模型文本始终是不可信输入，即使系统消息明确要求 JSON。
    payload = json.loads(model.complete(messages))
    if not isinstance(payload, dict):
        raise ValueError("model response must be a JSON object")
    # 本章只校验根节点；字段是否齐全、类型和值域是否合法，需要后续结构化校验。
    return payload


def main() -> int:
    """运行单条成功示例，或用 --cases 对照关键词规则的漏判与误判。"""

    parser = argparse.ArgumentParser(description="离线演示模型端口与关键词基线")
    parser.add_argument("--cases", action="store_true", help="运行四条教学对照消息")
    args = parser.parse_args()

    if args.cases:
        # 对照人工标签观察漏判和误判；这些样本用于教学，不代表真实准确率。
        cases = [
            ("Please refund order SO-1", "refund"),
            ("I was charged twice. Can I get my money back?", "refund"),
            ("Please do not refund order SO-1", "other"),
            ("Where is my invoice?", "other"),
        ]
        for user_text, expected in cases:
            actual = classify(RuleBasedModel(), user_text)["intent"]
            print(f"expected={expected} actual={actual} text={user_text}")
        return 0

    result = classify(RuleBasedModel(), "Please refund order SO-1")
    print(f"intent={result['intent']} confidence={result['confidence']}")
    print("provider=protocol")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
