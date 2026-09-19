"""CH14-EX01 自动验收。"""

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_plain_json_object_is_parsed() -> None:
    assert target.parse_model_object('{"intent":"refund"}', {"intent"}) == {
        "intent": "refund"
    }


def test_json_code_fence_is_removed() -> None:
    text = '```json\n{"answer": 42}\n```'
    assert target.parse_model_object(text, {"answer"}) == {"answer": 42}


@pytest.mark.parametrize("text", ["not-json", "[1, 2]"])
def test_invalid_or_non_object_output_is_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        target.parse_model_object(text, set())


def test_missing_required_field_is_reported() -> None:
    with pytest.raises(ValueError, match="intent"):
        target.parse_model_object('{"answer":"ok"}', {"intent"})
