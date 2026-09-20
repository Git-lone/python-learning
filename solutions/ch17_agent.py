"""CH17-EX01 参考答案。"""

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
    # 预算按模型决策计数，最终答案也占一步，工具错误后继续同样会消耗剩余预算。
    for step in range(1, max_steps + 1):
        # tuple 限制历史序列的增删，不会冻结事件中的嵌套参数对象。
        action = model.next_action(tuple(history))
        if isinstance(action, FinalAnswer):
            return AgentResult(action.text, tuple(history), step)
        history.append(action)
        handler = tools.get(action.name)
        if handler is None:
            # 白名单之外的名称永不执行，只形成可见的拒绝观察。
            history.append(ToolObservation(action.name, None, "tool not allowed"))
            continue
        try:
            result = handler(action.arguments)
        except Exception as error:
            # 教学版保留简短消息；生产版应映射稳定错误码并清理敏感信息。
            history.append(ToolObservation(action.name, None, str(error)))
        else:
            history.append(ToolObservation(action.name, result))
    # 步数预算是 Agent 最基本的失控保护。
    raise StepLimitError(f"agent exceeded {max_steps} steps")
