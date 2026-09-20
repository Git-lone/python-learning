"""一个最小但完整的 Agent 循环：决策、工具、观察、结束。"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ToolCall:
    name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FinalAnswer:
    text: str


@dataclass(frozen=True, slots=True)
class ToolObservation:
    name: str
    result: object
    error: str | None = None


Action = ToolCall | FinalAnswer
Event = ToolCall | ToolObservation
ToolHandler = Callable[[Mapping[str, object]], object]


class AgentModel(Protocol):
    def next_action(self, history: Sequence[Event]) -> Action: ...


@dataclass(frozen=True, slots=True)
class AgentResult:
    answer: str
    history: tuple[Event, ...]
    steps: int


class StepLimitError(RuntimeError):
    """Agent 未在预算内结束。"""


def run_agent(
    model: AgentModel, tools: Mapping[str, ToolHandler], max_steps: int = 4
) -> AgentResult:
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    history: list[Event] = []
    # 一步指一次模型决策，返回最终答案也占一步，不等于工具调用次数。
    for step in range(1, max_steps + 1):
        # 模型只能提出动作；循环仍由确定性代码掌握控制权。
        # tuple 防止模型增删这份历史序列，但 arguments 等嵌套对象并未深度冻结。
        action = model.next_action(tuple(history))
        if isinstance(action, FinalAnswer):
            return AgentResult(action.text, tuple(history), step)
        history.append(action)
        handler = tools.get(action.name)
        if handler is None:
            # 未知工具作为观察返回，绝不能退化为反射、eval 或 shell 执行。
            history.append(ToolObservation(action.name, None, "tool not allowed"))
            continue
        try:
            result = handler(action.arguments)
        except Exception as error:
            # 工具错误进入轨迹，模型下一步可以选择修正参数或结束。
            # 教学示例直接记录异常文本；接入真实服务前需对错误信息脱敏。
            history.append(ToolObservation(action.name, None, str(error)))
        else:
            history.append(ToolObservation(action.name, result))
    # 硬上限保证错误模型不会造成无限工具调用和费用增长。
    raise StepLimitError(f"agent exceeded {max_steps} steps")


class DemoModel:
    def next_action(self, history: Sequence[Event]) -> Action:
        if not history:
            return ToolCall("add", {"left": 2, "right": 3})
        observation = history[-1]
        assert isinstance(observation, ToolObservation)
        return FinalAnswer(f"2 + 3 = {observation.result}")


def add(arguments: Mapping[str, object]) -> int:
    # 此处简化校验会接受 bool，因为 bool 是 int 子类；严格版本见 CH15 的 add。
    left = arguments.get("left")
    right = arguments.get("right")
    if not isinstance(left, int) or not isinstance(right, int):
        raise ValueError("integer arguments required")
    return left + right


def main() -> int:
    result = run_agent(DemoModel(), {"add": add})
    observation = result.history[-1]
    assert isinstance(observation, ToolObservation)
    print(f"tool={observation.name} result={observation.result}")
    print(f"final={result.answer} steps={result.steps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
