"""安全编码 SSE，正文换行不能伪造事件。实现后运行本章验收；不要先复制参考答案。"""


def encode_sse(event: str, payload: dict[str, object]) -> str:
    # 返回一条完整 SSE 消息，以空行结束；事件名只能包含小写英文字母与下划线。
    # 正文是 JSON，含换行的字符串也必须留在同一条消息内，非法事件名报 ValueError。
    raise NotImplementedError("Implement CH23-EX01")
