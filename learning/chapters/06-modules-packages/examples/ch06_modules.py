"""从包的公开 API 导入名称。"""

from order_tools import gross_total


def main() -> int:
    print(f"public_api={gross_total([10.0, 15.0]):.2f}")
    print(f"module_name={__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
