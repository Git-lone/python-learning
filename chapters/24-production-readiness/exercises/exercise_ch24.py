"""安全底线不能被平均指标掩盖。实现后运行本章验收；不要先复制参考答案。"""


def release_allowed(success_rate: float, p95_ms: float, permission_failures: int) -> bool:
    # 成功率使用 0..1，延迟单位为毫秒；阈值为成功率 >=0.9、P95 <=2000、权限失败为 0。
    # 无效测量值抛 ValueError；测量合法但未通过门禁则返回 False，不能混淆两者。
    raise NotImplementedError("Implement CH24-EX01")
