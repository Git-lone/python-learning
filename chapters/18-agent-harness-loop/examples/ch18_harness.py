"""演示 Harness 暂停高风险工具，并从检查点批准后恢复。"""

from collections.abc import Sequence

from harness_runtime import (
    Action,
    AgentHarness,
    FinalAnswer,
    HarnessLimits,
    HistoryEvent,
    ListEventSink,
    MemoryCheckpointStore,
    ToolCall,
    ToolObservation,
    ToolSpec,
)


class ReportModel:
    """离线模型：先发布周报，再根据工具观察给出最终答案。"""

    def next_action(
        self, objective: str, history: Sequence[HistoryEvent]
    ) -> Action:
        if not history:
            return ToolCall(
                call_id="publish-weekly-001",
                name="publish_report",
                arguments={"content": "本周完成 3 个任务"},
            )
        observation = history[-1]
        if isinstance(observation, ToolObservation) and observation.error is None:
            return FinalAnswer("周报已发布")
        return FinalAnswer("周报未发布")


def main() -> int:
    published: dict[str, str] = {}

    def publish_report(call: ToolCall) -> str:
        content = call.arguments.get("content")
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        # call_id 是幂等键；恢复或重试不会逻辑上重复发布同一份周报。
        published.setdefault(call.call_id, content)
        return "published"

    store = MemoryCheckpointStore()
    sink = ListEventSink()
    harness = AgentHarness(
        model=ReportModel(),
        tools={
            "publish_report": ToolSpec(
                publish_report,
                requires_approval=True,
            )
        },
        limits=HarnessLimits(max_steps=3, max_tool_calls=1),
        store=store,
        sink=sink,
        verifier=lambda answer: None if answer == "周报已发布" else "周报尚未发布",
    )

    # 首次运行在副作用发生前暂停，并把 pending_call 写入检查点。
    paused = harness.start("run-weekly-001", "发布本周任务进度")
    pending = paused.pending_call
    assert pending is not None
    print(f"paused={paused.status} pending={pending.call_id}")

    # 审批决定按 call_id 传入，恢复时执行的仍是原调用而不是重新询问模型。
    completed = harness.resume(
        paused.run_id,
        approvals={"publish-weekly-001": True},
    )
    print(
        f"completed={completed.status} answer={completed.answer} "
        f"tool_calls={completed.tool_calls}"
    )
    print(f"published={published['publish-weekly-001']}")
    print("events=" + ",".join(event.kind for event in sink.events))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
