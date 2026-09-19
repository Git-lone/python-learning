"""CH13-EX01 自动验收。"""

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_timeout_is_retried_then_json_object_is_returned() -> None:
    calls = 0

    def fetch() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("slow")
        return '{"ok": true}'

    assert target.load_json_with_retry(fetch, retries=1) == {"ok": True}
    assert calls == 2


def test_timeout_is_raised_after_budget_is_exhausted() -> None:
    def fetch() -> str:
        raise TimeoutError("still slow")

    with pytest.raises(TimeoutError):
        target.load_json_with_retry(fetch, retries=1)


@pytest.mark.parametrize("payload", ["not-json", "[1, 2]"])
def test_invalid_or_non_object_json_is_rejected(payload: str) -> None:
    with pytest.raises(ValueError):
        target.load_json_with_retry(lambda: payload)


def test_negative_retry_budget_is_rejected_before_fetch() -> None:
    with pytest.raises(ValueError):
        target.load_json_with_retry(lambda: "{}", retries=-1)
