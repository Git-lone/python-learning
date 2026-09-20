"""Reference answer for CH19; inspect only after attempting the exercise."""


def parse_usage(payload: dict[str, object]) -> tuple[int, int]:
    # 缺失用量意味着未知，不能默认为 0，否则成本统计会把未知请求当成免费。
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("usage missing")
    counts = usage.get("input_tokens"), usage.get("output_tokens")
    # 精确比较类型以拒绝 bool；or 短路保证字符串、None 不会参与大小比较。
    if any(type(value) is not int or value < 0 for value in counts):
        raise ValueError("invalid token counts")
    return counts
