"""CH18-EX01 参考答案：可恢复的 Agent Harness 循环。

模型提出动作，Harness 决定动作能否执行、是否需要审批以及何时终止。
本题用同步调用和内存对象演示控制流程；没有跨进程持久化、并发领取或调用超时控制。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Literal, Protocol


@dataclass(frozen=True, slots=True)
class ToolCall:
    """模型提出的工具调用；call_id 用于关联审批、检查点和工具幂等执行。

    call_id 由调用内容提供，Harness 不验证其唯一性，也不会自动给外部系统去重。
    """

    call_id: str
    name: str
    # frozen 与 Mapping 都不提供深度冻结，工具处理器不应修改传入的参数对象。
    arguments: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FinalAnswer:
    """模型提出的最终文本；是否完成任务仍由 Harness 的验收器决定。"""

    text: str


@dataclass(frozen=True, slots=True)
class ToolObservation:
    """工具执行反馈；用 call_id 对应原请求，error 为 None 时表示本次未报告错误。"""

    call_id: str
    name: str
    result: object
    error: str | None = None


@dataclass(frozen=True, slots=True)
class VerificationObservation:
    """答案未通过验收时的反馈，作为后续模型决策的上下文。"""

    feedback: str


# 联合类型表达有限动作集合；类型注解不会替代下方 isinstance 的运行时判断。
Action = ToolCall | FinalAnswer
HistoryEvent = ToolCall | ToolObservation | VerificationObservation
RunStatus = Literal["running", "waiting_approval", "completed", "failed"]
ToolHandler = Callable[[ToolCall], object]
# 验收器返回 None 表示通过，字符串则作为失败反馈进入下一轮模型上下文。
CompletionVerifier = Callable[[str], str | None]


class AgentModel(Protocol):
    """模型适配器的结构化接口，可类比 Java interface 的调用契约。

    Python Protocol 允许对象按方法形状满足接口，无需显式继承，便于注入假模型测试。
    """

    def next_action(
        self, objective: str, history: Sequence[HistoryEvent]
    ) -> Action:
        """读取目标及历史，提出一个工具调用或答案；此方法本身不执行工具。"""
        ...


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """把工具处理函数与审批策略放在一起，供工具注册表按名字查询。

    此处只有注册表准入和审批开关，没有用户权限判定或参数 Schema 校验。
    """

    handler: ToolHandler
    requires_approval: bool = False


@dataclass(frozen=True, slots=True)
class HarnessLimits:
    """约束有效模型动作数及实际进入工具处理器的次数。

    这是次数预算，不是 token、费用或耗时预算；构造时拒绝不可用的上限。
    """

    max_steps: int = 6
    max_tool_calls: int = 3

    def __post_init__(self) -> None:
        """dataclass 完成字段赋值后自动调用，集中验证配置的不变量。"""

        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        if self.max_tool_calls < 1:
            raise ValueError("max_tool_calls must be positive")


@dataclass(frozen=True, slots=True)
class RunState:
    """一次运行的检查点：同时保存历史、累计预算和等待处理的调用。

    frozen 与 tuple 便于用 replace 表达状态迁移；嵌套参数和工具结果仍可能可变。
    RunStatus 仅为类型提示，持久化适配器若接受外部数据仍需自行校验状态。
    """

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
    """记录控制流程中的事件，供观察暂停、恢复、验收等过程；不充当业务结果。"""

    run_id: str
    kind: str
    step: int
    detail: str


@dataclass(slots=True)
class MemoryCheckpointStore:
    """按 run_id 保存最新状态对象，方便同一进程里的 Harness 实例接续运行。

    字典保存对象引用，不做序列化或深复制；也没有锁、版本校验和并发更新保护。
    """

    # 只支持同一进程内恢复；跨进程恢复必须换用磁盘/数据库存储，见 CH21。
    states: dict[str, RunState] = field(default_factory=dict)

    def save(self, state: RunState) -> None:
        """覆盖该运行的最新检查点；旧版本是否可覆盖不在此教学存储中判断。"""

        self.states[state.run_id] = state

    def load(self, run_id: str) -> RunState | None:
        """返回已保存对象，未找到时返回 None，由上层决定报错或创建新运行。"""

        return self.states.get(run_id)


@dataclass(slots=True)
class ListEventSink:
    """把事件收集到内存列表，供示例和测试查看执行顺序，不提供持久化审计。"""

    events: list[RunEvent] = field(default_factory=list)

    def emit(self, event: RunEvent) -> None:
        """追加事件；不去重，也不承担消息投递确认。"""

        self.events.append(event)


def _accept_any_answer(answer: str) -> str | None:
    """默认验收器始终通过，仅用于让示例不依赖额外业务检查。"""

    # 默认不验收业务效果；真实任务应注入可查询、可验证的完成条件。
    return None


class AgentHarness:
    """用确定性规则托管模型决策、审批暂停、工具反馈和答案验收。

    start/resume 返回当前运行状态，可能完成、失败或暂停等待审批。
    模型与验收器异常会向上传播；工具异常才会被转换成供模型读取的观察结果。
    """

    def __init__(
        self,
        model: AgentModel,
        tools: Mapping[str, ToolSpec],
        limits: HarnessLimits,
        store: MemoryCheckpointStore,
        sink: ListEventSink,
        verifier: CompletionVerifier | None = None,
    ) -> None:
        """注入模型、工具注册表、预算、存储和事件接收器，使控制逻辑可以独立测试。"""

        self._model = model
        self._tools = tools
        self._limits = limits
        self._store = store
        self._sink = sink
        self._verifier = verifier or _accept_any_answer

    def start(self, run_id: str, objective: str) -> RunState:
        """创建非空且尚未存在的运行，立即推进到完成、失败或等待审批。

        查重和保存是两个操作，仅适用于本题串行使用，不能视为并发创建的原子防重。
        """

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
        """从检查点继续，用 call_id → 同意/拒绝 映射处理当前待审批调用。

        未提供决定仍会暂停；已完成或失败的运行不可恢复。调用方负责审批人的身份验证，
        本题不包含审批过期、参数签名或并发恢复保护。
        """

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
        """先处理已有调用，再请求下一次模型决策，直到遇到终态或审批暂停。

        待处理调用已经消耗过一次模型步骤，恢复执行它不会再次扣模型预算。
        """

        while True:
            # pending_call 已写入历史，恢复时直接执行，避免重复模型决策。
            if state.pending_call is not None:
                state = self._handle_call(state, state.pending_call, approvals)
                if state.status != "running":
                    return state
                continue

            if state.step >= self._limits.max_steps:
                return self._fail(state, "model step budget exhausted")

            # 本题同步等待模型，没有请求超时；抛错时保留最近检查点并把异常交给调用方。
            action = self._model.next_action(state.objective, state.history)
            if isinstance(action, FinalAnswer):
                state = replace(state, step=state.step + 1)
                self._record(state, "model_action", "final_answer")
                # 答案提案也消耗一步；仅返回文本不会自动证明外部业务已经完成。
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
        """依次检查注册表、工具预算和审批，再执行已批准的调用。

        未注册工具或审批拒绝只形成反馈，不计工具尝试；进入 handler 后即使失败也计数。
        """

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
        """追加工具反馈并清除待处理调用，使下一轮模型能依据结果决定后续动作。

        工具报错不直接终止运行；模型可能改参数或换工具，但仍受累计预算限制。
        """

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
        """保存不可继续的失败状态并清除待执行项，不回滚已经发生的外部副作用。"""

        failed = replace(
            state, status="failed", pending_call=None, answer=None, error=error
        )
        self._record(failed, "run_failed", error)
        return failed

    def _record(self, state: RunState, kind: str, detail: str) -> None:
        """先保存检查点再追加事件；两步没有原子性，事件接收失败时状态可能已更新。"""

        # 教学版先保存再发事件；跨系统生产实现通常使用事务 outbox。
        self._store.save(state)
        self._sink.emit(RunEvent(state.run_id, kind, state.step, detail))
