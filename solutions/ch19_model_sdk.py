"""CH19 参考答案：校验模拟模型响应中的 token 用量；建议先独立完成练习。"""


def parse_usage(payload: dict[str, object]) -> tuple[int, int]:
    """返回输入与输出 token 数；缺失、布尔值或负数均视为无效用量。

    此处只处理练习约定的字段结构，不执行 SDK 请求，也不计算价格或费用。
    """

    # 缺失用量意味着未知，不能默认为 0，否则成本统计会把未知请求当成免费。
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("usage missing")
    counts = usage.get("input_tokens"), usage.get("output_tokens")
    # 精确比较类型以拒绝 bool；or 短路保证字符串、None 不会参与大小比较。
    if any(type(value) is not int or value < 0 for value in counts):
        raise ValueError("invalid token counts")
    return counts
