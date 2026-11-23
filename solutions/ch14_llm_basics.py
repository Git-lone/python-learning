"""CH14-EX01 参考答案：把外部文本收敛为可供业务检查的 JSON 对象。

本模块只解析已获得的文本，不调用大模型，也不验证内容是否符合事实。
它演示的是模型响应进入业务代码之前的一层格式与字段检查。
"""

import json


def parse_model_object(text: str, required: set[str]) -> dict[str, object]:
    """接受纯 JSON 或完整代码围栏文本，返回包含 required 字段的字典。

    required 是必须出现的字段名集合；额外字段会被保留，字段值是否为
    空值、类型是否正确、业务上能否采用，都不属于这里的校验范围。
    """
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
        # from 保留异常原因链，作用类似 Java 包装异常时传入 cause。
        raise ValueError("model output is not valid JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("model output must be a JSON object")
    # 这里只检查字段存在，不保证值的类型或含义正确；业务 Schema 还需独立校验。
    # 排序让错误消息稳定，便于测试和日志聚合。
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    return payload
