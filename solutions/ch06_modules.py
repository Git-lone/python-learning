"""CH06-EX01 参考答案。"""


def build_order_id(prefix: str, sequence: int) -> str:
    normalized = prefix.strip().upper()
    if not normalized:
        raise ValueError("prefix must not be empty")
    if sequence < 0:
        raise ValueError("sequence must not be negative")
    return f"{normalized}-{sequence:06d}"
