"""供离线示例和单元测试使用的内存适配器。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import RunEvent, RunState


@dataclass(slots=True)
class MemoryCheckpointStore:
    """按 run_id 保留最新状态，便于观察 start/resume 如何衔接。

    这是普通内存 Map 的适配，不提供数据库事务、并发领取或历史版本存档。
    """

    # 每个存储实例有独立字典；这里只保存对象引用，不序列化、不支持进程重启恢复。
    states: dict[str, RunState] = field(default_factory=dict)

    def save(self, state: RunState) -> None:
        # RunState 顶层字段冻结，但嵌套参数仍可能可变，调用方不能把它当深拷贝快照。
        self.states[state.run_id] = state

    def load(self, run_id: str) -> RunState | None:
        return self.states.get(run_id)


@dataclass(slots=True)
class ListEventSink:
    """把事件保存在列表中，便于断言顺序和内容。"""

    # default_factory 让每个实例独立持有列表，避免多个运行示例意外共享事件容器。
    events: list[RunEvent] = field(default_factory=list)

    def emit(self, event: RunEvent) -> None:
        self.events.append(event)
