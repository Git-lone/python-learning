"""CH12-EX01 自动验收。"""

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_settings_are_parsed_from_environment() -> None:
    settings = target.load_settings(
        {"APP_HOST": "0.0.0.0", "APP_PORT": "8080", "APP_DEBUG": "true"}
    )
    assert settings == target.Settings("0.0.0.0", 8080, True)


def test_settings_have_safe_defaults() -> None:
    assert target.load_settings({}) == target.Settings("127.0.0.1", 8000, False)


@pytest.mark.parametrize("port", ["abc", "0", "65536"])
def test_invalid_port_is_rejected(port: str) -> None:
    with pytest.raises(ValueError):
        target.load_settings({"APP_PORT": port})


def test_unknown_boolean_is_rejected() -> None:
    with pytest.raises(ValueError):
        target.load_settings({"APP_DEBUG": "sometimes"})
