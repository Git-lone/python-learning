"""Harness 运行时使用的不可变领域模型。"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ToolCall:
    """模型提出的工具调用；call_id 同时充当幂等键。"""

    call_id: str
    name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FinalAnswer:
    """模型建议结束当前循环时给出的答案。"""

    text: str


@dataclass(frozen=True, slots=True)
class ToolObservation:
    """工具成功、拒绝或失败后反馈给模型的确定性观察。"""

    call_id: str
    name: str
    result: object
    error: str | None = None


@dataclass(frozen=True, slots=True)
class VerificationObservation:
    """完成条件未满足时反馈给模型的修正信息。"""

    feedback: str


Action = ToolCall | FinalAnswer
HistoryEvent = ToolCall | ToolObservation | VerificationObservation
RunStatus = Literal["running", "waiting_approval", "completed", "failed"]


@dataclass(frozen=True, slots=True)
class HarnessLimits:
    """Harness 强制执行的模型轮数和工具调用双重预算。"""

    max_steps: int = 6
    max_tool_calls: int = 3

    def __post_init__(self) -> None:
        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        if self.max_tool_calls < 1:
            raise ValueError("max_tool_calls must be positive")


@dataclass(frozen=True, slots=True)
class RunState:
    """足以暂停并恢复一次 Agent 运行的确定性状态。"""

    run_id: str
    objective: str
    status: RunStatus = "running"
    step: int = 0
    tool_calls: int = 0
    history: tuple[HistoryEvent, ...] = ()
    pending_call: ToolCall | None = None
    answer: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class RunEvent:
    """供日志、指标或 Trace 适配器消费的脱敏运行事件。"""

    run_id: str
    kind: str
    step: int
    detail: str
