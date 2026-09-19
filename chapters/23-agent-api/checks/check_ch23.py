import json

import pytest
from exercise_support import load_target

target = load_target(__file__)


def test_roundtrip_and_injection():
    text = 'hello\n\nevent: forged\ndata: secret\n"'
    wire = target.encode_sse("delta", {"text": text})
    assert wire.startswith("event: delta\ndata: ")
    assert wire.count("\n\n") == 1
    assert json.loads(wire.split("data: ", 1)[1]) == {"text": text}


@pytest.mark.parametrize("name", ["", "delta\nevent: forged", "done\r", "has space"])
def test_bad_event_name(name):
    with pytest.raises(ValueError):
        target.encode_sse(name, {})
