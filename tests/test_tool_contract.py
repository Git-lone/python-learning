"""第 15 章工具建议边界回归；不混入学习者的注册表练习验收。"""

import importlib
from pathlib import Path

import pytest


@pytest.fixture
def contract(monkeypatch):
    """按直接运行示例时的导入路径加载相邻模块，不依赖练习是否完成。"""

    examples = (
        Path(__file__).resolve().parents[1]
        / "chapters/15-structured-output-tools/examples"
    )
    monkeypatch.syspath_prepend(str(examples))
    return importlib.import_module("ch15_tool_contract")


@pytest.mark.parametrize(
    ("case_name", "expected_stage", "expected_events"),
    [
        ("bad-parameters", "tool-parameters", ["entered"]),
        ("unknown-tool", "allowlist", []),
        ("invalid-structure", "request-contract", []),
    ],
)
def test_rejection_stops_at_the_expected_boundary(
    contract, case_name, expected_stage, expected_events
) -> None:
    events = []

    def tracked_add(arguments):
        # 区分“进入处理器”和“完成运算”；坏参数会进入前者，不能到达后者。
        events.append("entered")
        result = contract.add(arguments)
        events.append("completed")
        return result

    registry = contract.ToolRegistry()
    registry.register("add", tracked_add)
    observation = contract.run_suggestion(registry, contract.CASES[case_name])
    assert events == expected_events
    assert observation["status"] == "rejected"
    assert observation["stage"] == expected_stage
    assert "result" not in observation


@pytest.mark.parametrize(
    "raw",
    [
        'null',
        '{"name":"add"}',
        '{"name":42,"arguments":{}}',
        '{"name":"  ","arguments":{}}',
        '{"name":"add","arguments":{},"execute":true}',
    ],
)
def test_invalid_envelopes_are_rejected_before_dispatch(contract, raw) -> None:
    # 空注册表也应报输入合同错误，而不是抢先报“工具不存在”。
    observation = contract.run_suggestion(contract.ToolRegistry(), raw)
    assert observation["status"] == "rejected"
    assert observation["stage"] == "request-contract"


def test_handler_key_error_is_not_reported_as_unknown_tool(contract) -> None:
    def broken_handler(arguments):
        raise KeyError("missing_internal_data")

    registry = contract.ToolRegistry()
    registry.register("add", broken_handler)
    with pytest.raises(KeyError, match="missing_internal_data"):
        contract.run_suggestion(registry, contract.CASES["success"])
