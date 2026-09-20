"""CH18-EX01 参考答案：可恢复的 Agent Harness 循环。"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Literal, Protocol


@dataclass(frozen=True, slots=True)
class ToolCall:
    """call_id 用于关联审批、检查点和工具幂等执行。"""

    call_id: str
    name: str
    # frozen 与 Mapping 都不提供深度冻结，工具处理器不应修改传入的参数对象。
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
# 验收器返回 None 表示通过，字符串则作为失败反馈进入下一轮模型上下文。
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
    # 只支持同一进程内恢复；跨进程恢复必须换用磁盘/数据库存储，见 CH21。
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
    # 默认不验收业务效果；真实任务应注入可查询、可验证的完成条件。
    return None


class AgentHarness:
    """用确定性规则托管概率模型的执行循环。"""

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
        # 不可变状态通过 replace 生成新实例，恢复时沿用历史和已经消耗的预算。
        state = replace(state, status="running")
        self._record(state, "run_resumed", "checkpoint loaded")
        return self._drive(state, approvals or {})

    def _drive(self, state: RunState, approvals: Mapping[str, bool]) -> RunState:
        while True:
            # pending_call 已写入历史，恢复时直接执行，避免重复模型决策。
            if state.pending_call is not None:
                state = self._handle_call(state, state.pending_call, approvals)
                if state.status != "running":
                    return state
                continue

            if state.step >= self._limits.max_steps:
                return self._fail(state, "model step budget exhausted")

            action = self._model.next_action(state.objective, state.history)
            if isinstance(action, FinalAnswer):
                state = replace(state, step=state.step + 1)
                self._record(state, "model_action", "final_answer")
                feedback = self._verifier(action.text)
                if feedback is None:
                    completed = replace(
                        state, status="completed", answer=action.text, error=None
                    )
                    self._record(completed, "run_completed", "verified answer")
                    return completed
                # 验收结果进入上下文，让模型可以在剩余预算内继续修正。
                state = replace(
                    state,
                    history=(*state.history, VerificationObservation(feedback)),
                )
                self._record(state, "verification_failed", feedback)
                continue

            if not isinstance(action, ToolCall):
                return self._fail(state, "model returned an invalid action")

            # 执行前保存调用，使暂停后保留同一个 call_id；内存实现不能跨进程恢复。
            state = replace(
                state,
                step=state.step + 1,
                history=(*state.history, action),
                pending_call=action,
            )
            self._record(state, "model_action", f"tool:{action.name}")

    def _handle_call(
        self, state: RunState, call: ToolCall, approvals: Mapping[str, bool]
    ) -> RunState:
        spec = self._tools.get(call.name)
        if spec is None:
            return self._observe(state, call, None, "tool not allowed")
        if state.tool_calls >= self._limits.max_tool_calls:
            return self._fail(state, "tool call budget exhausted")

        if spec.requires_approval:
            # 未收到决定时暂停；明确拒绝时形成观察，且绝不能调用处理器。
            decision = approvals.get(call.call_id)
            if decision is None:
                paused = replace(state, status="waiting_approval")
                self._record(paused, "approval_requested", f"tool:{call.name}")
                return paused
            if not decision:
                return self._observe(state, call, None, "approval denied")

        try:
            # 外部副作用与状态保存之间存在中断窗口，工具自身仍需按 call_id 实现幂等。
            result = spec.handler(call)
        except Exception as error:
            # 已进入 handler 的失败尝试同样计入工具预算。
            return self._observe(
                replace(state, tool_calls=state.tool_calls + 1),
                call,
                None,
                f"tool failed: {error}",
            )
        return self._observe(
            replace(state, tool_calls=state.tool_calls + 1), call, result, None
        )

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
        # 教学版先保存再发事件；跨系统生产实现通常使用事务 outbox。
        self._store.save(state)
        self._sink.emit(RunEvent(state.run_id, kind, state.step, detail))
