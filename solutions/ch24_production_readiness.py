"""Reference answer for CH24; inspect only after attempting the exercise."""

import math


def release_allowed(success_rate: float, p95_ms: float, permission_failures: int) -> bool:
    # 先拒绝 NaN/无穷大等无效测量值，不能仅依赖数值大小比较。
    if not math.isfinite(success_rate) or not 0 <= success_rate <= 1:
        raise ValueError("invalid success_rate")
    if not math.isfinite(p95_ms) or p95_ms < 0 or permission_failures < 0:
        raise ValueError("invalid measurements")
    # 门禁是同时满足，而非加权平均；权限失败不能被高成功率或低延迟抵消。
    return success_rate >= 0.9 and p95_ms <= 2000 and permission_failures == 0
