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
    # Mapping 是只读接口提示，frozen 也只限制字段赋值；嵌套字典没有被深度冻结。
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
# Literal 辅助静态检查，合法状态迁移仍必须由运行时代码保证。
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
    # step 统计模型决策，tool_calls 统计真正进入处理器的尝试，两种预算不能混用。
    step: int = 0
    tool_calls: int = 0
    history: tuple[HistoryEvent, ...] = ()
    # 已有决策但尚未完成的工具调用；恢复时优先处理它，避免再次让模型生成动作。
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
