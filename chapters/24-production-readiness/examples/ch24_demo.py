from decimal import Decimal
from agent_lab.operations import estimate_cost, release_allowed

if __name__ == "__main__":
    # 2 和 8 是演示费率，不是真实报价；从字符串创建 Decimal 保持十进制精度。
    print("illustrative_cost=" + str(estimate_cost(1000, 200, Decimal("2"), Decimal("8"))))
    # 即使成功率和延迟达标，出现一次权限错误也不能通过本例发布门禁。
    print("release_with_permission_failure=" + str(release_allowed(1, 100, 1)))
