"""CH02-EX01 自动验收。"""

from exercise_support import load_target

target = load_target(__file__)


def test_even_squares_filters_odd_numbers_and_deduplicates_keys() -> None:
    assert target.even_squares([1, 2, 2, 3, 4]) == {2: 4, 4: 16}


def test_even_squares_accepts_one_shot_iterators() -> None:
    assert target.even_squares(iter([2, 5, 6])) == {2: 4, 6: 36}


def test_even_squares_handles_empty_input() -> None:
    assert target.even_squares([]) == {}
