"""Reference answer for CH20; inspect only after attempting the exercise."""


def read_ticket(result: dict[str, object]) -> str:
    if result.get("isError") is not False:
        raise ValueError("tool error or missing status")
    payload = result.get("structuredContent")
    if not isinstance(payload, dict) or payload.get("ticket_id") != "DEMO-1":
        raise ValueError("unexpected ticket")
    if payload.get("status") != "waiting_for_customer":
        raise ValueError("invalid status")
    return payload["status"]
