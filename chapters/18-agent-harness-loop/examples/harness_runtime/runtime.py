"""确定性的 Agent Harness：驱动循环并托管所有安全边界。"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from .models import (
    FinalAnswer,
    HarnessLimits,
    RunEvent,
    RunState,
    ToolCall,
    ToolObservation,
    VerificationObservation,
)
from .ports import (
    AgentModel,
    CheckpointStore,
    CompletionVerifier,
    EventSink,
    ToolRegistry,
)


def _accept_any_answer(answer: str) -> str | None:
    """默认完成检查；业务项目应注入可验证的验收条件。"""

    return None


class AgentHarness:
    """在模型外部管理循环、预算、审批、检查点和事件。"""

    def __init__(
        self,
        model: AgentModel,
        tools: ToolRegistry,
        limits: HarnessLimits,
        store: CheckpointStore,
        sink: EventSink,
        verifier: CompletionVerifier | None = None,
    ) -> None:
        self._model = model
        self._tools = tools
        self._limits = limits
        self._store = store
        self._sink = sink
        self._verifier = verifier or _accept_any_answer

    def start(self, run_id: str, objective: str) -> RunState:
        """创建新运行；重复 run_id 会被拒绝，避免覆盖已有检查点。"""

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
        """从检查点恢复暂停或意外中断的运行。"""

        state = self._store.load(run_id)
        if state is None:
            raise KeyError(f"run not found: {run_id}")
        if state.status not in {"running", "waiting_approval"}:
            raise ValueError(f"run cannot be resumed from status: {state.status}")
        state = replace(state, status="running")
        self._record(state, "run_resumed", "checkpoint loaded")
        return self._drive(state, approvals or {})

    def _drive(self, state: RunState, approvals: Mapping[str, bool]) -> RunState:
        """持续推进状态，直到完成、失败或需要人工审批。"""

        while True:
            # 恢复时先处理已持久化的调用，不能让模型重新生成另一个动作。
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
                # 模型不能自行宣布任务成功；确定性验收失败后继续循环。
                state = replace(
                    state,
                    history=(*state.history, VerificationObservation(feedback)),
                )
                self._record(state, "verification_failed", feedback)
                continue

            if not isinstance(action, ToolCall):
                return self._fail(state, "model returned an invalid action")

            # 在执行前持久化动作，因此进程重启后仍可从同一个 call_id 恢复。
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
            decision = approvals.get(call.call_id)
            if decision is None:
                paused = replace(state, status="waiting_approval")
                self._record(paused, "approval_requested", f"tool:{call.name}")
                return paused
            if not decision:
                return self._observe(state, call, None, "approval denied")

        try:
            # 即使工具抛错，也会消耗一次调用预算；外部副作用应使用 call_id 幂等。
            result = spec.handler(call)
        except Exception as error:
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
        observation = ToolObservation(
            call_id=call.call_id,
            name=call.name,
            result=result,
            error=error,
        )
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
        # 先保存状态，再发布事件；生产实现还需要事务或 outbox 保证原子性。
        self._store.save(state)
        self._sink.emit(RunEvent(state.run_id, kind, state.step, detail))
