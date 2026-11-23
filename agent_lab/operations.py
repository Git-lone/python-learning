"""第 24 章运营约束练习：将 token 用量换算为成本，并校验示例发布门槛。

这里是纯函数演算，不负责采集监控数据，也不实际执行发布。费率、成功率和延迟都
由调用方提供；示例阈值用于讨论工程决策，不是厂商报价或适用于所有业务的 SLA。
"""

from decimal import Decimal
import math


def estimate_cost(
    input_tokens: int, output_tokens: int, input_per_million: Decimal, output_per_million: Decimal
) -> Decimal:
    """按输入、输出各自的每百万 token 费率估算费用，使用 Decimal 保持十进制精度。

    类比 Java BigDecimal，费率宜由字符串构造。调用方须先拿到真实用量并统一
    费率币种；未知用量不应当作零。本函数不覆盖缓存折扣、工具计费或重试汇总。
    """

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
    """对已汇总的质量、延迟和权限失败数做联合判断，不在这里计算原始指标。

    success_rate 需先定义成功与样本分母，p95_ms 是第 95 百分位延迟而不是平均值。
    只有三项均满足示例门槛才返回 True，返回值仍须由上层发布流程使用才会生效。
    """

    # NaN/无穷大不是有效测量，先校验再比较发布阈值。
    if not math.isfinite(success_rate) or not 0 <= success_rate <= 1:
        raise ValueError("success_rate must be finite and between 0 and 1")
    if not math.isfinite(p95_ms) or p95_ms < 0 or permission_failures < 0:
        raise ValueError("invalid measurements")
    # 示例门禁要求三项同时通过；权限隔离失败不能用较好的平均指标抵消。
    return success_rate >= 0.9 and p95_ms <= 2000 and permission_failures == 0
