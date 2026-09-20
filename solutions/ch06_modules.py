"""CH06-EX01 参考答案。"""


def build_order_id(prefix: str, sequence: int) -> str:
    # 先规范化再校验，才能拒绝仅含空白的前缀。
    normalized = prefix.strip().upper()
    if not normalized:
        raise ValueError("prefix must not be empty")
    if sequence < 0:
        raise ValueError("sequence must not be negative")
    # 06d 表示十进制整数至少六位，不足补零；超过六位不会被截断。
    return f"{normalized}-{sequence:06d}"
