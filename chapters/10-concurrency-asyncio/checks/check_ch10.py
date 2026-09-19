"""CH10-EX01 自动验收。"""

import asyncio

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_run_limited_preserves_order_and_enforces_limit() -> None:
    async def scenario() -> tuple[list[int], int]:
        active = 0
        peak = 0

        async def work(value: int, delay: float) -> int:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            try:
                await asyncio.sleep(delay)
                return value
            finally:
                active -= 1

        results = await target.run_limited(
            [work(1, 0.03), work(2, 0.01), work(3, 0.01)],
            limit=2,
        )
        return results, peak

    results, peak = asyncio.run(scenario())
    assert results == [1, 2, 3]
    assert peak == 2


def test_invalid_limit_is_rejected() -> None:
    with pytest.raises(ValueError):
        asyncio.run(target.run_limited([], limit=0))
