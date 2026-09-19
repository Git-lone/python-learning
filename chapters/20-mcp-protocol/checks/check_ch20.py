import pytest
from exercise_support import load_target

target = load_target(__file__)


def test_valid():
    assert (
        target.read_ticket(
            {
                "isError": False,
                "structuredContent": {"ticket_id": "DEMO-1", "status": "waiting_for_customer"},
            }
        )
        == "waiting_for_customer"
    )


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"isError": True},
        {"isError": False},
        {"isError": False, "structuredContent": {"ticket_id": "OTHER"}},
        {"isError": False, "structuredContent": {"ticket_id": "DEMO-1", "status": None}},
    ],
)
def test_invalid(value):
    with pytest.raises(ValueError):
        target.read_ticket(value)
