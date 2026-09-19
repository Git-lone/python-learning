"""用协议隔离模型供应商，并把模型文本视作不可信输入。"""

from collections.abc import Sequence
from dataclasses import dataclass
import json
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
    return payload


def main() -> int:
    result = classify(RuleBasedModel(), "Please refund order SO-1")
    print(f"intent={result['intent']} confidence={result['confidence']}")
    print("provider=protocol")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
