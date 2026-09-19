from decimal import Decimal
from agent_lab.operations import estimate_cost, release_allowed

if __name__ == "__main__":
    print("illustrative_cost=" + str(estimate_cost(1000, 200, Decimal("2"), Decimal("8"))))
    print("release_with_permission_failure=" + str(release_allowed(1, 100, 1)))
