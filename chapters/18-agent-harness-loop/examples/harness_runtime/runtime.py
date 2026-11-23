"""确定性的 Agent Harness：驱动循环并集中执行预算、审批与完成检查。

主线为 start/resume → _drive → _handle_call → _observe → _drive。
模型建议动作，Harness 推进状态；这个同步教学实现不包含生产鉴权、分布式租约或事务幂等。
"""

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
    """在模型外部管理循环、预算、审批、检查点和事件。

    构造参数相当于注入 Java Service 的协作接口，便于替换模型、存储或观测实现。
    一次调用返回 completed、failed 或 waiting_approval；等待审批也是正常返回结果。
    """

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

        # 先检查再保存只适用于当前串行演示；并发启动同一 ID 需要存储侧原子唯一约束。
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
        """从已有检查点继续推进，保留已消耗预算和原 pending_call。

        approvals 是上层提供的决定，映射本身没有用户身份、有效期或参数签名校验。
        若仍未提供原调用的审批，循环会再次返回等待状态，而不是默认放行。
        """

        state = self._store.load(run_id)
        if state is None:
            raise KeyError(f"run not found: {run_id}")
        if state.status not in {"running", "waiting_approval"}:
            raise ValueError(f"run cannot be resumed from status: {state.status}")
        # replace 创建新的 dataclass 实例，保留原有历史和预算，不修改旧状态的字段。
        state = replace(state, status="running")
        self._record(state, "run_resumed", "checkpoint loaded")
        return self._drive(state, approvals or {})

    def _drive(self, state: RunState, approvals: Mapping[str, bool]) -> RunState:
        """持续推进状态，直到完成、失败或需要人工审批。"""

        while True:
            # 恢复时先处理检查点中保存的调用，不能让模型重新生成另一个动作。
            if state.pending_call is not None:
                state = self._handle_call(state, state.pending_call, approvals)
                if state.status != "running":
                    return state
                # 工具处理已写入观察并清空 pending_call，下一次迭代才重新请求模型。
                continue

            if state.step >= self._limits.max_steps:
                return self._fail(state, "model step budget exhausted")

            action = self._model.next_action(state.objective, state.history)
            # 模型接口异常会向调用方传播；这里的 failed 状态并不覆盖所有外部故障。
            if isinstance(action, FinalAnswer):
                state = replace(state, step=state.step + 1)
                self._record(state, "model_action", "final_answer")
                # None 才是通过；失败反馈写入历史，让模型在剩余预算内继续处理。
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

            # 执行前保存动作；只有接入持久化存储，进程重启后才能恢复同一个 call_id。
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
        """按白名单、工具预算、审批的顺序检查原调用，再把执行结果转为观察。

        未注册或被拒绝的工具不会进入处理器，也不消耗工具调用计数；提出它的模型决策已计步。
        """

        spec = self._tools.get(call.name)
        if spec is None:
            return self._observe(state, call, None, "tool not allowed")
        if state.tool_calls >= self._limits.max_tool_calls:
            return self._fail(state, "tool call budget exhausted")

        if spec.requires_approval:
            # 无决定(None)、明确拒绝(False)、同意(True)是三种状态，不能合并成真假判断。
            decision = approvals.get(call.call_id)
            if decision is None:
                paused = replace(state, status="waiting_approval")
                self._record(paused, "approval_requested", f"tool:{call.name}")
                return paused
            if not decision:
                return self._observe(state, call, None, "approval denied")

        try:
            # 即使工具抛错，也会消耗一次调用预算；外部副作用应使用 call_id 幂等。
            # 工具成功与下一次保存状态之间仍可能中断，检查点本身不保证恰好执行一次。
            result = spec.handler(call)
        except Exception as error:
            # 示例保留错误文本；真实模型上下文中的错误信息也要脱敏，不只是日志。
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
        """追加一次成功或失败观察并回到 running，让模型依据执行事实决定下一步。"""

        observation = ToolObservation(
            call_id=call.call_id,
            name=call.name,
            result=result,
            error=error,
        )
        # 工具结果入历史后清空 pending_call，下一轮才允许请求新的模型动作。
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
        """把运行收敛到失败终态；清除待执行动作，避免把预算失败当成可继续审批。"""

        failed = replace(
            state, status="failed", pending_call=None, answer=None, error=error
        )
        self._record(failed, "run_failed", error)
        return failed

    def _record(self, state: RunState, kind: str, detail: str) -> None:
        """保存当前快照并发送摘要事件；这两个端口调用都可能抛错，示例不做自动重试。"""

        # 先保存状态，再发布事件；生产实现还需要事务或 outbox 保证原子性。
        self._store.save(state)
        self._sink.emit(RunEvent(state.run_id, kind, state.step, detail))
