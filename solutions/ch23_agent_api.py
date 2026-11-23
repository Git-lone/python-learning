"""第 23 章参考解答：把一条应用事件编码为 SSE 文本。

请先独立完成练习再阅读。本题负责消息格式；HTTP 响应头、身份验证、断线
重连、事件持久化和审批恢复由 API 与业务层另行实现。
"""

import json
import re


def encode_sse(event: str, payload: dict[str, object]) -> str:
    """返回包含事件名、JSON 数据和结束空行的一条 SSE 消息。

    event 只接受小写英文字母和下划线，非法名称抛出 ValueError。payload
    中的值必须能被 JSON 序列化；类型注解中的 object 不代表任意 Python
    对象都可以发送。此处不检查业务字段，调用方仍需按事件契约校验载荷。
    """
    # 事件名不能包含换行，避免用户输入伪造额外的 event/data 字段。
    if not re.fullmatch(r"[a-z_]+", event):
        raise ValueError("invalid event name")
    # JSON 会转义正文中的换行；最后的空行才是 SSE 消息边界。
    # ensure_ascii=True 将非 ASCII 字符写成转义序列，客户端解析 JSON 后还原。
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=True)}\n\n"
