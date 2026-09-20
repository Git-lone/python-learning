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
# 返回 None 表示验收通过，返回字符串表示需要反馈给模型的失败原因。
CompletionVerifier = Callable[[str], str | None]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """工具实现与执行策略，策略不交给模型决定。"""

    handler: ToolHandler
    # 审批策略由应用注册工具时指定，而不是接受模型参数中的自报权限。
    requires_approval: bool = False


class CheckpointStore(Protocol):
    """保存可恢复状态的端口；生产环境可以接数据库或工作流引擎。"""

    def save(self, state: RunState) -> None: ...

    def load(self, run_id: str) -> RunState | None: ...


class EventSink(Protocol):
    """接收运行事件的端口；事件正文不应携带提示词或敏感参数。"""

    def emit(self, event: RunEvent) -> None: ...


ToolRegistry = Mapping[str, ToolSpec]
