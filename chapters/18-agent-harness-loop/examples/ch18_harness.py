"""演示 Harness 暂停高风险工具，并从检查点批准后恢复。

阅读顺序：先看 main 的工具注册与两次运行，再进入 runtime.AgentHarness._drive。
ReportModel 只提出发布请求；Harness 决定是否执行，工具负责产生实际副作用。
这里用内存字典模拟发布结果，整个示例不会向外部系统发送周报。
"""

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
        """根据有无历史提出请求，再按工具观察结束；objective 在这个固定替身中未参与决策。"""

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
    """装配端口适配器，先运行到等待审批，再带明确决定恢复同一任务。"""

    published: dict[str, str] = {}

    def publish_report(call: ToolCall) -> str:
        """把已批准的调用写入内存结果表；返回值作为观察反馈给模型。"""

        content = call.arguments.get("content")
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        # call_id 演示幂等：同一进程内不重复插入，但不会校验同一键的正文是否变更。
        # 跨进程持久化与载荷冲突校验见 CH21，不能把内存字典当成生产幂等存储。
        published.setdefault(call.call_id, content)
        return "published"

    # 这里只演示同一进程内的暂停/恢复；进程退出后内存检查点就丢失。
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
        # 文本匹配仅用于演示；真实验收应查询业务状态，不能只相信模型声称已完成。
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
    # 工具完成后还要再让模型决策并通过 verifier，状态才从 running 变为 completed。
    print(
        f"completed={completed.status} answer={completed.answer} "
        f"tool_calls={completed.tool_calls}"
    )
    print(f"published={published['publish-weekly-001']}")
    print("events=" + ",".join(event.kind for event in sink.events))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
