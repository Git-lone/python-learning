"""第 24 章参考解答：用三个独立条件判断评测结果是否通过发布门禁。

请先独立完成练习再阅读。阈值是本题的约定，不是通用生产标准；真实发布
还需要结合业务风险、样本覆盖、指标来源以及回滚方案制定放行条件。
"""

import math


def release_allowed(success_rate: float, p95_ms: float, permission_failures: int) -> bool:
    """校验已统计的指标并返回是否放行，不计算指标或执行部署。

    success_rate 使用 0 到 1 的比例，p95_ms 使用毫秒，permission_failures
    表示评测发现的权限失败次数。有效指标未达到门槛时返回 False；无效
    测量值抛出 ValueError，让调用方区分效果不达标与评测数据有问题。

    零次权限失败只代表这批样本未发现问题，不证明所有调用都具备正确授权。
    """
    # 先拒绝 NaN/无穷大等无效测量值，不能仅依赖数值大小比较。
    if not math.isfinite(success_rate) or not 0 <= success_rate <= 1:
        raise ValueError("invalid success_rate")
    if not math.isfinite(p95_ms) or p95_ms < 0 or permission_failures < 0:
        raise ValueError("invalid measurements")
    # 门禁是同时满足，而非加权平均；权限失败不能被高成功率或低延迟抵消。
    return success_rate >= 0.9 and p95_ms <= 2000 and permission_failures == 0
