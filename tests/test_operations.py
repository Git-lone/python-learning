from decimal import Decimal

import pytest

from agent_lab.operations import estimate_cost, release_allowed


def test_cost_uses_explicit_rates_and_both_token_directions():
    assert estimate_cost(1000, 200, Decimal("2"), Decimal("8")) == Decimal("0.0036")
    with pytest.raises(ValueError):
        estimate_cost(True, 0, Decimal("2"), Decimal("8"))
    with pytest.raises(ValueError):
        estimate_cost(10, 0, Decimal("NaN"), Decimal("8"))


def test_release_gate_never_averages_away_permission_failure():
    assert release_allowed(0.9, 2000, 0)
    assert not release_allowed(1, 10, 1)
    assert not release_allowed(0.89, 10, 0)
    assert not release_allowed(1, 2001, 0)
    with pytest.raises(ValueError):
        release_allowed(float("nan"), 10, 0)
