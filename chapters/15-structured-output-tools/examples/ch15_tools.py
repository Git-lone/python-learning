"""显式工具注册表：名称白名单、参数边界和统一执行入口。

可以把 ToolRegistry 看成 Java 的 Map<String, Function<...>>：
模型只提供名称与参数，应用决定哪些函数能被调用，具体工具再校验业务参数。
main 中使用固定 JSON 模拟模型请求，尚未接入真实模型或通用请求结构校验器。
"""

from collections.abc import Callable, Mapping
import json

ToolHandler = Callable[[Mapping[str, object]], object]


class UnknownToolError(KeyError):
    """名称未注册；仍兼容 KeyError，且不会与处理器内部的缺键错误混淆。"""


class ToolRegistry:
    """保存应用显式注册的函数；注册和执行职责分开，便于统一限制能力范围。"""

    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        """把工具名绑定到处理函数；空名称与重名都视为配置错误。"""

        # 注册表就是工具白名单；重复名称可能悄悄改变安全边界。
        if not name or name in self._tools:
            raise ValueError(f"invalid or duplicate tool: {name}")
        self._tools[name] = handler

    def execute(self, name: str, arguments: Mapping[str, object]) -> object:
        """按名称调用已注册函数并原样返回结果；未知名称与工具异常继续向上抛出。"""

        try:
            handler = self._tools[name]
        except KeyError as error:
            raise UnknownToolError(f"unknown tool: {name}") from error
        # 注册表负责名称白名单；参数校验仍由具体工具负责，异常由上层循环处理。
        return handler(arguments)


def add(arguments: Mapping[str, object]) -> int:
    """从动态参数中读取两个整数，校验后相加；类型标注不会替代这些运行时检查。"""

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
    """串起 JSON 解码、白名单分派、参数校验和结果返回四个边界。"""

    registry = ToolRegistry()
    registry.register("add", add)
    call = json.loads('{"name":"add","arguments":{"left":2,"right":3}}')
    # 固定教学输入已知含有这两个字段；真实模型响应还需校验根类型、必填项及参数结构。
    result = registry.execute(call["name"], call["arguments"])
    print(f"tool={call['name']} result={result}")
    print("allowlist=enabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
