"""CH14-EX01 参考答案。"""

import json


def parse_model_object(text: str, required: set[str]) -> dict[str, object]:
    normalized = text.strip()
    # 仅移除完整的 Markdown 围栏，不猜测或改写围栏内的 JSON。
    if normalized.startswith("```") and normalized.endswith("```"):
        lines = normalized.splitlines()
        if len(lines) < 3:
            raise ValueError("empty JSON code fence")
        normalized = "\n".join(lines[1:-1]).strip()
    try:
        payload = json.loads(normalized)
    except json.JSONDecodeError as error:
        raise ValueError("model output is not valid JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("model output must be a JSON object")
    # 这里只检查字段存在，不保证值的类型或含义正确；业务 Schema 还需独立校验。
    # 排序让错误消息稳定，便于测试和日志聚合。
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    return payload
