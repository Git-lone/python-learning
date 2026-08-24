"""CH09-EX01 自动验收。"""

import pytest

from learning.exercise_support import load_target

target = load_target(__file__)


def test_chunked_preserves_tail_batch() -> None:
    assert list(target.chunked(range(5), 2)) == [[0, 1], [2, 3], [4]]


def test_chunked_handles_empty_iterable() -> None:
    assert list(target.chunked([], 3)) == []


def test_invalid_size_is_rejected_when_iteration_starts() -> None:
    chunks = target.chunked([1], 0)
    with pytest.raises(ValueError):
        next(chunks)
