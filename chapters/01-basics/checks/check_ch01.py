"""CH01-EX01 自动验收。"""

from exercise_support import load_target

target = load_target(__file__)


def test_bulk_order_is_formatted_with_two_decimals() -> None:
    assert target.describe_order(19.99, 3) == "quantity=3 total=59.97 size=bulk"


def test_small_order_is_normal() -> None:
    assert target.describe_order(20.0, 1) == "quantity=1 total=20.00 size=normal"
