"""Reference answer for CH20; inspect only after attempting the exercise."""


def read_ticket(result: dict[str, object]) -> str:
    # 传输成功不代表工具成功；缺少状态也不能当成功，必须明确为布尔 False。
    if result.get("isError") is not False:
        raise ValueError("tool error or missing status")
    # 读取结构化结果而非解析展示文本；本练习只接受约定的模拟工单及其状态。
    payload = result.get("structuredContent")
    if not isinstance(payload, dict) or payload.get("ticket_id") != "DEMO-1":
        raise ValueError("unexpected ticket")
    if payload.get("status") != "waiting_for_customer":
        raise ValueError("invalid status")
    return payload["status"]
