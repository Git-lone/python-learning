"""CH18-EX01 自动验收。"""

from collections.abc import Sequence
from typing import Any

from exercise_support import load_target

target = load_target(__file__)


def test_harness_executes_tool_checkpoints_events_and_finishes() -> None:
    class Model:
        def next_action(self, objective: str, history: Sequence[object]) -> object:
            if not history:
                return target.ToolCall("lookup-1", "lookup", {"key": "status"})
            return target.FinalAnswer("done")

    store = target.MemoryCheckpointStore()
    sink = target.ListEventSink()
    harness = target.AgentHarness(
        Model(),
        {"lookup": target.ToolSpec(lambda call: call.arguments["key"])},
        target.HarnessLimits(max_steps=3, max_tool_calls=2),
        store,
        sink,
    )

    result = harness.start("run-1", "查询任务状态")

    assert result.status == "completed"
    assert result.answer == "done"
    assert result.step == 2
    assert result.tool_calls == 1
    assert result.history[-1] == target.ToolObservation(
        "lookup-1", "lookup", "status"
    )
    assert store.load("run-1") == result
    assert [event.kind for event in sink.events] == [
        "run_started",
        "model_action",
        "tool_result",
        "model_action",
        "run_completed",
    ]


def test_sensitive_tool_pauses_then_resumes_same_call_after_approval() -> None:
    executed: list[str] = []

    class Model:
        def next_action(self, objective: str, history: Sequence[object]) -> object:
            if not history:
                return target.ToolCall("publish-1", "publish", {})
            return target.FinalAnswer("published")

    def publish(call: Any) -> str:
        executed.append(call.call_id)
        return "ok"

    store = target.MemoryCheckpointStore()
    sink = target.ListEventSink()
    harness = target.AgentHarness(
        Model(),
        {"publish": target.ToolSpec(publish, requires_approval=True)},
        target.HarnessLimits(),
        store,
        sink,
    )

    paused = harness.start("run-2", "发布报告")
    assert paused.status == "waiting_approval"
    assert paused.pending_call.call_id == "publish-1"
    assert executed == []
    assert store.load("run-2") == paused

    completed = harness.resume("run-2", {"publish-1": True})
    assert completed.status == "completed"
    assert completed.pending_call is None
    assert executed == ["publish-1"]


def test_denied_approval_becomes_observation_without_side_effect() -> None:
    executed = False

    class Model:
        def next_action(self, objective: str, history: Sequence[object]) -> object:
            if not history:
                return target.ToolCall("delete-1", "delete", {})
            return target.FinalAnswer("cancelled")

    def delete(call: object) -> None:
        nonlocal executed
        executed = True

    store = target.MemoryCheckpointStore()
    harness = target.AgentHarness(
        Model(),
        {"delete": target.ToolSpec(delete, requires_approval=True)},
        target.HarnessLimits(),
        store,
        target.ListEventSink(),
    )

    harness.start("run-3", "删除文件")
    result = harness.resume("run-3", {"delete-1": False})

    assert result.status == "completed"
    assert executed is False
    observation = result.history[-1]
    assert observation.error == "approval denied"


def test_tool_budget_stops_loop_before_second_execution() -> None:
    executed: list[str] = []

    class Model:
        def next_action(self, objective: str, history: Sequence[object]) -> object:
            index = sum(isinstance(event, target.ToolCall) for event in history) + 1
            return target.ToolCall(f"call-{index}", "work", {})

    def work(call: Any) -> str:
        executed.append(call.call_id)
        return "ok"

    harness = target.AgentHarness(
        Model(),
        {"work": target.ToolSpec(work)},
        target.HarnessLimits(max_steps=4, max_tool_calls=1),
        target.MemoryCheckpointStore(),
        target.ListEventSink(),
    )

    result = harness.start("run-4", "持续工作")

    assert result.status == "failed"
    assert result.error == "tool call budget exhausted"
    assert executed == ["call-1"]


def test_failed_completion_check_returns_feedback_to_loop() -> None:
    class Model:
        def next_action(self, objective: str, history: Sequence[object]) -> object:
            if not history:
                return target.FinalAnswer("draft")
            assert isinstance(history[-1], target.VerificationObservation)
            return target.FinalAnswer("verified")

    harness = target.AgentHarness(
        Model(),
        {},
        target.HarnessLimits(max_steps=2, max_tool_calls=1),
        target.MemoryCheckpointStore(),
        target.ListEventSink(),
        verifier=lambda answer: None if answer == "verified" else "not verified",
    )

    result = harness.start("run-5", "生成并验证答案")

    assert result.status == "completed"
    assert result.answer == "verified"
    assert result.history == (target.VerificationObservation("not verified"),)
