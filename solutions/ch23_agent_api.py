"""Reference answer for CH23; inspect only after attempting the exercise."""

import json
import re


def encode_sse(event: str, payload: dict[str, object]) -> str:
    if not re.fullmatch(r"[a-z_]+", event):
        raise ValueError("invalid event name")
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=True)}\n\n"
