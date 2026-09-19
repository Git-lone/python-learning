import pytest
from exercise_support import load_target

target = load_target(__file__)


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"usage": {"input_tokens": 12, "output_tokens": 3}}, (12, 3)),
        ({"usage": {"input_tokens": 0, "output_tokens": 0}}, (0, 0)),
    ],
)
def test_valid(payload, expected):
    assert target.parse_usage(payload) == expected


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"usage": None},
        {"usage": {}},
        {"usage": {"input_tokens": True, "output_tokens": 1}},
        {"usage": {"input_tokens": -1, "output_tokens": 1}},
        {"usage": {"input_tokens": "12", "output_tokens": 1}},
    ],
)
def test_invalid(payload):
    with pytest.raises(ValueError):
        target.parse_usage(payload)
