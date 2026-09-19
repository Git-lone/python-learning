"""CH17-EX01 自动验收。"""

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_agent_executes_tool_records_observation_and_finishes() -> None:
    class Model:
        def next_action(self, history: object) -> object:
            if not history:
                return target.ToolCall("echo", {"value": "ok"})
            return target.FinalAnswer("done")

    result = target.run_agent(Model(), {"echo": lambda arguments: arguments["value"]})
    assert result.answer == "done"
    assert result.steps == 2
    assert result.history[-1] == target.ToolObservation("echo", "ok")


def test_unknown_tool_becomes_observation_instead_of_execution() -> None:
    class Model:
        def next_action(self, history: object) -> object:
            if not history:
                return target.ToolCall("delete_everything", {})
            return target.FinalAnswer("refused")

    result = target.run_agent(Model(), {})
    observation = result.history[-1]
    assert observation.name == "delete_everything"
    assert observation.error == "tool not allowed"


def test_endless_agent_is_stopped_by_step_budget() -> None:
    class Model:
        def next_action(self, history: object) -> object:
            return target.ToolCall("noop", {})

    with pytest.raises(target.StepLimitError):
        target.run_agent(Model(), {"noop": lambda arguments: None}, max_steps=2)


def test_non_positive_step_budget_is_rejected() -> None:
    class Model:
        def next_action(self, history: object) -> object:
            return target.FinalAnswer("unused")

    with pytest.raises(ValueError):
        target.run_agent(Model(), {}, max_steps=0)
