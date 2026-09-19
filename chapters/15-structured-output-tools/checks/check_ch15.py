"""CH15-EX01 自动验收。"""

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_registered_tool_receives_arguments_and_returns_result() -> None:
    registry = target.ToolRegistry()
    registry.register("echo", lambda arguments: arguments["value"])
    assert registry.execute("echo", {"value": "ok"}) == "ok"


def test_unknown_tool_is_rejected() -> None:
    with pytest.raises(KeyError, match="missing"):
        target.ToolRegistry().execute("missing", {})


def test_duplicate_tool_name_is_rejected() -> None:
    registry = target.ToolRegistry()
    registry.register("echo", lambda arguments: arguments)
    with pytest.raises(ValueError):
        registry.register("echo", lambda arguments: arguments)


def test_empty_tool_name_is_rejected() -> None:
    with pytest.raises(ValueError):
        target.ToolRegistry().register("", lambda arguments: arguments)
