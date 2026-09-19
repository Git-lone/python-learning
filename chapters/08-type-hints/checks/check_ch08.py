"""CH08-EX01 自动验收。"""

from exercise_support import load_target

target = load_target(__file__)


def test_first_item_is_returned() -> None:
    assert target.first_or_none(["first", "second"]) == "first"


def test_empty_input_returns_none() -> None:
    assert target.first_or_none(iter(())) is None


def test_function_does_not_consume_past_first_item() -> None:
    consumed: list[int] = []

    def values() -> object:
        for number in (1, 2):
            consumed.append(number)
            yield number

    assert target.first_or_none(values()) == 1
    assert consumed == [1]
