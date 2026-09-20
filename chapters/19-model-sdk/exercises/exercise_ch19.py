"""解析真实 usage，拒绝伪造零用量。实现后运行本章验收；不要先复制参考答案。"""


def parse_usage(payload: dict[str, object]) -> tuple[int, int]:
    # 输入是含 usage 对象的响应；返回 (input_tokens, output_tokens)，每项为非负整数。
    # 缺失字段、bool 或其他非法类型抛 ValueError；未知用量不能默认为 0。
    raise NotImplementedError("Implement CH19-EX01")
