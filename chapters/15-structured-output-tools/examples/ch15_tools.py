"""显式工具注册表：名称白名单、参数边界和统一执行入口。"""

from collections.abc import Callable, Mapping
import json

ToolHandler = Callable[[Mapping[str, object]], object]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        # 注册表就是工具白名单；重复名称可能悄悄改变安全边界。
        if not name or name in self._tools:
            raise ValueError(f"invalid or duplicate tool: {name}")
        self._tools[name] = handler

    def execute(self, name: str, arguments: Mapping[str, object]) -> object:
        try:
            handler = self._tools[name]
        except KeyError as error:
            raise KeyError(f"unknown tool: {name}") from error
        # 注册表负责名称白名单；参数校验仍由具体工具负责，异常由上层循环处理。
        return handler(arguments)


def add(arguments: Mapping[str, object]) -> int:
    # bool 是 int 的子类，工具参数校验需要显式排除 True/False。
    left = arguments.get("left")
    right = arguments.get("right")
    if (
        isinstance(left, bool)
        or not isinstance(left, int)
        or isinstance(right, bool)
        or not isinstance(right, int)
    ):
        raise ValueError("left and right must be integers")
    return left + right


def main() -> int:
    registry = ToolRegistry()
    registry.register("add", add)
    call = json.loads('{"name":"add","arguments":{"left":2,"right":3}}')
    result = registry.execute(call["name"], call["arguments"])
    print(f"tool={call['name']} result={result}")
    print("allowlist=enabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
