"""从包的公开 API 导入名称。"""

# 调用方只依赖包公开的名称，不必知道计算逻辑放在 pricing 子模块中。
from order_tools import gross_total


def main() -> int:
    print(f"public_api={gross_total([10.0, 15.0]):.2f}")
    print(f"module_name={__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
