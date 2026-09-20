"""Reference answer for CH23; inspect only after attempting the exercise."""

import json
import re


def encode_sse(event: str, payload: dict[str, object]) -> str:
    # 事件名不能包含换行，避免用户输入伪造额外的 event/data 字段。
    if not re.fullmatch(r"[a-z_]+", event):
        raise ValueError("invalid event name")
    # JSON 会转义正文中的换行；最后的空行才是 SSE 消息边界。
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=True)}\n\n"
