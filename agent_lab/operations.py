"""Small interview exercises in accounting and release gates, not vendor prices."""

from decimal import Decimal
import math


def estimate_cost(
    input_tokens: int, output_tokens: int, input_per_million: Decimal, output_per_million: Decimal
) -> Decimal:
    if type(input_tokens) is not int or type(output_tokens) is not int:
        raise ValueError("token counts must be integers")
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts must be nonnegative")
    if any(not rate.is_finite() or rate < 0 for rate in (input_per_million, output_per_million)):
        raise ValueError("rates must be finite and nonnegative")
    return (input_tokens * input_per_million + output_tokens * output_per_million) / 1_000_000


def release_allowed(success_rate: float, p95_ms: float, permission_failures: int) -> bool:
    if not math.isfinite(success_rate) or not 0 <= success_rate <= 1:
        raise ValueError("success_rate must be finite and between 0 and 1")
    if not math.isfinite(p95_ms) or p95_ms < 0 or permission_failures < 0:
        raise ValueError("invalid measurements")
    return success_rate >= 0.9 and p95_ms <= 2000 and permission_failures == 0
