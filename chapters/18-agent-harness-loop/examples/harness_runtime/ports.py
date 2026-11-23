"""Harness 与模型、工具、存储及观测系统之间的端口。

可按 Java 的接口与依赖注入理解：runtime 依赖这些合同，adapters 提供具体实现。
Protocol 按方法结构匹配，不要求适配器显式继承；类型提示也不替代运行时参数校验。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from .models import Action, HistoryEvent, RunEvent, RunState, ToolCall


class AgentModel(Protocol):
    """真实模型 SDK 只需适配这个最小决策端口。"""

    def next_action(
        self, objective: str, history: Sequence[HistoryEvent]
    ) -> Action:
        """读取目标和累计观察，仅提出下一动作；工具执行由 Harness 接管。"""

        ...


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
    """保存可恢复状态的端口；生产环境可以接数据库或工作流引擎。

    当前合同只有读写，没有版本号、CAS 或事务接口，不能据此保证多个执行者互斥。
    真实持久化适配还需处理对象序列化、存储故障，以及快照与工具版本的兼容。
    """

    def save(self, state: RunState) -> None: ...

    def load(self, run_id: str) -> RunState | None: ...


class EventSink(Protocol):
    """接收运行事件的端口；事件正文不应携带提示词或敏感参数。

    事件用于解释执行过程；恢复以 CheckpointStore 为依据，不能把日志自动等同于检查点。
    """

    def emit(self, event: RunEvent) -> None: ...


ToolRegistry = Mapping[str, ToolSpec]
