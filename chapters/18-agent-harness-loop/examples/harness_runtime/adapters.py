"""供离线示例和单元测试使用的内存适配器。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import RunEvent, RunState


@dataclass(slots=True)
class MemoryCheckpointStore:
    """按 run_id 保存最新不可变快照。"""

    states: dict[str, RunState] = field(default_factory=dict)

    def save(self, state: RunState) -> None:
        self.states[state.run_id] = state

    def load(self, run_id: str) -> RunState | None:
        return self.states.get(run_id)


@dataclass(slots=True)
class ListEventSink:
    """把事件保存在列表中，便于断言顺序和内容。"""

    events: list[RunEvent] = field(default_factory=list)

    def emit(self, event: RunEvent) -> None:
        self.events.append(event)
