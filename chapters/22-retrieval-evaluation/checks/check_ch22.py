import pytest
from exercise_support import load_target

target = load_target(__file__)


@pytest.mark.parametrize(
    "retrieved,relevant,k,expected",
    [
        (["a", "a", "b"], {"a", "b"}, 2, 0.5),
        (["x", "a"], {"a"}, 1, 0),
        ([], {"a"}, 3, 0),
        (["a", "b"], {"a", "b"}, 5, 1),
    ],
)
def test_metric(retrieved, relevant, k, expected):
    assert target.recall_at_k(retrieved, relevant, k) == expected


@pytest.mark.parametrize("relevant,k", [(set(), 3), ({"a"}, 0), ({"a"}, -1)])
def test_invalid(relevant, k):
    with pytest.raises(ValueError):
        target.recall_at_k([], relevant, k)
