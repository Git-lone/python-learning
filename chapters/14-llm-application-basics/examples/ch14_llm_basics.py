"""用协议隔离模型供应商，并把模型文本视作不可信输入。"""

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True, slots=True)
class Message:
    role: Role
    content: str


class ModelClient(Protocol):
    def complete(self, messages: Sequence[Message]) -> str: ...


class RuleBasedModel:
    def complete(self, messages: Sequence[Message]) -> str:
        # 离线替身保持模型端口真实，同时让测试结果完全确定。
        text = messages[-1].content.lower()
        # 这里是关键词规则，0.92 也是固定样例值，不代表真实模型置信度或效果。
        intent = "refund" if "refund" in text else "other"
        return json.dumps({"intent": intent, "confidence": 0.92})


def classify(model: ModelClient, user_text: str) -> dict[str, object]:
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
