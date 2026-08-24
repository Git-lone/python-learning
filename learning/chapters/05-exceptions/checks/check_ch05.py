"""CH05-EX01 自动验收。"""

import pytest

from learning.exercise_support import load_target

target = load_target(__file__)


def test_positive_integer_is_returned() -> None:
    assert target.require_positive_quantity("3") == 3


def test_conversion_error_is_chained() -> None:
    with pytest.raises(target.InvalidQuantityError) as captured:
        target.require_positive_quantity("abc")
    assert isinstance(captured.value.__cause__, ValueError)


@pytest.mark.parametrize("raw", ["0", "-1"])
def test_non_positive_integer_is_rejected(raw: str) -> None:
    with pytest.raises(target.InvalidQuantityError, match="positive"):
        target.require_positive_quantity(raw)
