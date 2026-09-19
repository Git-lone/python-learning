"""Harness 与模型、工具、存储及观测系统之间的端口。"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from .models import Action, HistoryEvent, RunEvent, RunState, ToolCall


class AgentModel(Protocol):
    """真实模型 SDK 只需适配这个最小决策端口。"""

    def next_action(
        self, objective: str, history: Sequence[HistoryEvent]
    ) -> Action: ...


ToolHandler = Callable[[ToolCall], object]
CompletionVerifier = Callable[[str], str | None]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """工具实现与执行策略，策略不交给模型决定。"""

    handler: ToolHandler
    requires_approval: bool = False


class CheckpointStore(Protocol):
    """保存可恢复状态的端口；生产环境可以接数据库或工作流引擎。"""

    def save(self, state: RunState) -> None: ...

    def load(self, run_id: str) -> RunState | None: ...


class EventSink(Protocol):
    """接收运行事件的端口；事件正文不应携带提示词或敏感参数。"""

    def emit(self, event: RunEvent) -> None: ...


ToolRegistry = Mapping[str, ToolSpec]
