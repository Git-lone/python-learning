"""CH11-EX01 自动验收。"""

from decimal import Decimal

from learning.exercise_support import load_target

target = load_target(__file__)


def test_student_test_is_complete_and_passes() -> None:
    target.test_discount_never_becomes_negative()


def test_fixed_discount_boundary_really_returns_zero() -> None:
    assert target.fixed_discount(Decimal("5"), Decimal("8")) == Decimal("0")
