"""CH03-EX01 自动验收。"""

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_discount_closure_captures_rate_and_rounds_result() -> None:
    discount = target.make_discount(0.2)
    assert discount(99.99) == 79.99
    assert discount(10.0) == 8.0


@pytest.mark.parametrize("rate", [-0.01, 1.01])
def test_discount_rejects_rate_outside_closed_interval(rate: float) -> None:
    with pytest.raises(ValueError):
        target.make_discount(rate)


def test_zero_and_full_discount_are_valid() -> None:
    assert target.make_discount(0)(10.0) == 10.0
    assert target.make_discount(1)(10.0) == 0.0
