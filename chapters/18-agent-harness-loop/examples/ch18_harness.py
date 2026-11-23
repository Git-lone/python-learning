"""演示 Harness 暂停高风险工具，并从检查点批准后恢复。

阅读顺序：先看 _run_demo 的工具注册与两次运行，再进入 runtime.AgentHarness._drive。
ReportModel 只提出发布请求；Harness 决定是否执行，工具负责产生实际副作用。
这里用内存字典模拟发布结果，整个示例不会向外部系统发送周报。
"""

import argparse
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


def _run_demo(decision: str, show_trace: bool) -> None:
    """运行一个独立场景；比较批准与拒绝时，各自使用全新的业务记录和检查点。"""

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

    def verify_publication(answer: str) -> str | None:
        """同时核对模拟业务记录和回答，避免把模型声称成功当作已发生的副作用。"""

        if published.get("publish-weekly-001") != "本周完成 3 个任务":
            return "周报尚未发布"
        return None if answer == "周报已发布" else "模型回答与发布记录不一致"

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
        # 本例查询内存业务表；真实发布系统需把这里替换为权威结果查询。
        verifier=verify_publication,
    )

    # 首次运行在副作用发生前暂停，并把 pending_call 写入检查点。
    paused = harness.start("run-weekly-001", "发布本周任务进度")
    pending = paused.pending_call
    assert pending is not None
    print(f"paused={paused.status} pending={pending.call_id}")
    if show_trace:
        print(
            f"checkpoint step={paused.step} tool_calls={paused.tool_calls} "
            f"published_count={len(published)}"
        )

    # 审批决定按 call_id 传入，恢复时执行的仍是原调用而不是重新询问模型。
    completed = harness.resume(
        paused.run_id,
        approvals={pending.call_id: decision == "approve"},
    )
    # 工具完成后还要再让模型决策并通过 verifier，状态才从 running 变为 completed。
    print(
        f"completed={completed.status} answer={completed.answer} "
        f"tool_calls={completed.tool_calls}"
    )
    # 拒绝没有写入记录；不要索引不存在的键，也不要把“正常返回”误当成任务成功。
    print(f"published={published.get(pending.call_id, '<none>')}")
    print("events=" + ",".join(event.kind for event in sink.events))

    if show_trace:
        print(
            f"decision={decision} steps={completed.step} tool_calls={completed.tool_calls} "
            f"published_count={len(published)} error={completed.error}"
        )
        # 事件说明控制流程，观察说明模型下一步实际看到了什么，两者不能相互替代。
        for event in sink.events:
            print(f"trace step={event.step} event={event.kind} detail={event.detail}")
        for item in completed.history:
            if isinstance(item, ToolObservation):
                print(
                    f"observation call_id={item.call_id} tool={item.name} "
                    f"result={item.result} error={item.error}"
                )


def main() -> int:
    """选择批准、拒绝或对照运行；默认批准且不展开轨迹，保留原来的输出。"""

    parser = argparse.ArgumentParser(description="观察 Harness 审批、恢复与完成验证")
    parser.add_argument(
        "--decision", choices=("approve", "deny", "both"), default="approve",
        help="批准、拒绝，或依次对照两个独立场景（默认 approve）",
    )
    parser.add_argument("--trace", action="store_true", help="展示检查点、预算、事件和工具观察")
    args = parser.parse_args()
    decisions = ("approve", "deny") if args.decision == "both" else (args.decision,)
    for decision in decisions:
        if len(decisions) > 1:
            print(f"scenario={decision}")
        _run_demo(decision, args.trace)
    # 拒绝场景的 failed 是预期教学结果；脚本本身完整跑完，因此退出码仍为 0。
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
