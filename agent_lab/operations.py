"""Small interview exercises in accounting and release gates, not vendor prices."""

from decimal import Decimal
import math


def estimate_cost(
    input_tokens: int, output_tokens: int, input_per_million: Decimal, output_per_million: Decimal
) -> Decimal:
    # bool 是 int 子类，但不能充当用量；精确类型检查也拒绝字符串和浮点数量。
    if type(input_tokens) is not int or type(output_tokens) is not int:
        raise ValueError("token counts must be integers")
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts must be nonnegative")
    if any(not rate.is_finite() or rate < 0 for rate in (input_per_million, output_per_million)):
        raise ValueError("rates must be finite and nonnegative")
    # 费率单位是每百万 token，使用 Decimal 累加；这里没有真实厂商报价或折扣规则。
    return (input_tokens * input_per_million + output_tokens * output_per_million) / 1_000_000


def release_allowed(success_rate: float, p95_ms: float, permission_failures: int) -> bool:
    # NaN/无穷大不是有效测量，先校验再比较发布阈值。
    if not math.isfinite(success_rate) or not 0 <= success_rate <= 1:
        raise ValueError("success_rate must be finite and between 0 and 1")
    if not math.isfinite(p95_ms) or p95_ms < 0 or permission_failures < 0:
        raise ValueError("invalid measurements")
    # 示例门禁要求三项同时通过；权限隔离失败不能用较好的平均指标抵消。
    return success_rate >= 0.9 and p95_ms <= 2000 and permission_failures == 0
