"""练习：实现有工具白名单和步数上限的 Agent 循环。"""

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
    """循环请求动作、执行白名单工具、记录观察，直到模型返回最终答案。"""
    # TODO 1：校验 max_steps，并维护只追加的 history。
    # TODO 2：处理 FinalAnswer、未知工具、成功结果和工具异常。
    # TODO 3：耗尽预算仍未结束时抛出 StepLimitError。
    raise NotImplementedError("请完成 CH17-EX01")
