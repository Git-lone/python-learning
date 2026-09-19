import pytest
from exercise_support import load_target

target = load_target(__file__)


@pytest.mark.parametrize(
    "rate,p95,failures,expected",
    [
        (0.9, 2000, 0, True),
        (0.899, 100, 0, False),
        (1, 2001, 0, False),
        (1, 1, 1, False),
    ],
)
def test_gate(rate, p95, failures, expected):
    assert target.release_allowed(rate, p95, failures) is expected


@pytest.mark.parametrize(
    "rate,p95,failures",
    [
        (float("nan"), 1, 0),
        (1, float("inf"), 0),
        (1.1, 1, 0),
        (1, -1, 0),
        (1, 1, -1),
    ],
)
def test_invalid(rate, p95, failures):
    with pytest.raises(ValueError):
        target.release_allowed(rate, p95, failures)
