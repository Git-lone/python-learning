"""CH06-EX01 自动验收。"""

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_order_id_normalizes_prefix_and_pads_sequence() -> None:
    assert target.build_order_id(" so ", 42) == "SO-000042"


@pytest.mark.parametrize("prefix", ["", "   "])
def test_empty_prefix_is_rejected(prefix: str) -> None:
    with pytest.raises(ValueError):
        target.build_order_id(prefix, 1)


def test_negative_sequence_is_rejected() -> None:
    with pytest.raises(ValueError):
        target.build_order_id("SO", -1)
