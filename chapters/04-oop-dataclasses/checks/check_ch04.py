"""CH04-EX01 自动验收。"""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_same_currency_addition_returns_new_money() -> None:
    left = target.Money(Decimal("10"), "EUR")
    right = target.Money(Decimal("5"), "EUR")
    assert left + right == target.Money(Decimal("15"), "EUR")
    assert left.amount == Decimal("10")


def test_different_currencies_are_rejected() -> None:
    with pytest.raises(ValueError):
        target.Money(Decimal("10"), "EUR") + target.Money(Decimal("5"), "USD")


def test_money_is_immutable() -> None:
    money = target.Money(Decimal("10"), "EUR")
    with pytest.raises(FrozenInstanceError):
        money.amount = Decimal("11")
