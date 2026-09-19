"""练习：实现可暂停、可恢复、可观测的 Agent Harness 循环。"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Literal, Protocol


@dataclass(frozen=True, slots=True)
class ToolCall:
    """模型建议调用工具，call_id 用于审批和幂等。"""

    call_id: str
    name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FinalAnswer:
    text: str


@dataclass(frozen=True, slots=True)
class ToolObservation:
    call_id: str
    name: str
    result: object
    error: str | None = None


@dataclass(frozen=True, slots=True)
class VerificationObservation:
    feedback: str


Action = ToolCall | FinalAnswer
HistoryEvent = ToolCall | ToolObservation | VerificationObservation
RunStatus = Literal["running", "waiting_approval", "completed", "failed"]
ToolHandler = Callable[[ToolCall], object]
CompletionVerifier = Callable[[str], str | None]


class AgentModel(Protocol):
    def next_action(
        self, objective: str, history: Sequence[HistoryEvent]
    ) -> Action: ...


@dataclass(frozen=True, slots=True)
class ToolSpec:
    handler: ToolHandler
    requires_approval: bool = False


@dataclass(frozen=True, slots=True)
class HarnessLimits:
    max_steps: int = 6
    max_tool_calls: int = 3

    def __post_init__(self) -> None:
        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        if self.max_tool_calls < 1:
            raise ValueError("max_tool_calls must be positive")


@dataclass(frozen=True, slots=True)
class RunState:
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
    run_id: str
    kind: str
    step: int
    detail: str


@dataclass(slots=True)
class MemoryCheckpointStore:
    """练习使用内存快照；接口形状可以替换为数据库实现。"""

    states: dict[str, RunState] = field(default_factory=dict)

    def save(self, state: RunState) -> None:
        self.states[state.run_id] = state

    def load(self, run_id: str) -> RunState | None:
        return self.states.get(run_id)


@dataclass(slots=True)
class ListEventSink:
    events: list[RunEvent] = field(default_factory=list)

    def emit(self, event: RunEvent) -> None:
        self.events.append(event)


def _accept_any_answer(answer: str) -> str | None:
    return None


class AgentHarness:
    """模型外部的确定性控制层。"""

    def __init__(
        self,
        model: AgentModel,
        tools: Mapping[str, ToolSpec],
        limits: HarnessLimits,
        store: MemoryCheckpointStore,
        sink: ListEventSink,
        verifier: CompletionVerifier | None = None,
    ) -> None:
        self._model = model
        self._tools = tools
        self._limits = limits
        self._store = store
        self._sink = sink
        self._verifier = verifier or _accept_any_answer

    def start(self, run_id: str, objective: str) -> RunState:
        if not run_id.strip() or not objective.strip():
            raise ValueError("run_id and objective must not be blank")
        if self._store.load(run_id) is not None:
            raise ValueError(f"run already exists: {run_id}")
        state = RunState(run_id=run_id, objective=objective)
        self._record(state, "run_started", "new run")
        return self._drive(state, approvals={})

    def resume(
        self, run_id: str, approvals: Mapping[str, bool] | None = None
    ) -> RunState:
        state = self._store.load(run_id)
        if state is None:
            raise KeyError(f"run not found: {run_id}")
        if state.status not in {"running", "waiting_approval"}:
            raise ValueError(f"run cannot be resumed from status: {state.status}")
        state = replace(state, status="running")
        self._record(state, "run_resumed", "checkpoint loaded")
        return self._drive(state, approvals or {})

    def _drive(self, state: RunState, approvals: Mapping[str, bool]) -> RunState:
        """推进模型动作，直到完成、失败或暂停。"""

        # TODO 1：恢复时先处理 pending_call，不能重复请求模型动作。
        # TODO 2：强制 max_steps，并处理工具动作、最终答案和非法动作。
        # TODO 3：最终答案必须通过 verifier；失败反馈要加入 history 后继续。
        raise NotImplementedError("请完成 CH18-EX01 的 Harness loop")

    def _handle_call(
        self, state: RunState, call: ToolCall, approvals: Mapping[str, bool]
    ) -> RunState:
        """执行白名单、预算与审批策略，再把结果封装成观察。"""

        # TODO 4：拒绝未知工具，并严格限制 max_tool_calls。
        # TODO 5：高风险工具无决定时暂停；拒绝时不得执行 handler。
        # TODO 6：成功和异常都写入观察；实际执行（包括异常）消耗工具预算。
        raise NotImplementedError("请完成 CH18-EX01 的工具控制层")

    def _observe(
        self,
        state: RunState,
        call: ToolCall,
        result: object,
        error: str | None,
    ) -> RunState:
        observation = ToolObservation(call.call_id, call.name, result, error)
        running = replace(
            state,
            status="running",
            history=(*state.history, observation),
            pending_call=None,
        )
        outcome = "error" if error is not None else "ok"
        self._record(running, "tool_result", f"{call.name}:{outcome}")
        return running

    def _fail(self, state: RunState, error: str) -> RunState:
        failed = replace(
            state, status="failed", pending_call=None, answer=None, error=error
        )
        self._record(failed, "run_failed", error)
        return failed

    def _record(self, state: RunState, kind: str, detail: str) -> None:
        # 检查点和脱敏事件由 Harness 统一产生，业务工具无需了解观测后端。
        self._store.save(state)
        self._sink.emit(RunEvent(state.run_id, kind, state.step, detail))
