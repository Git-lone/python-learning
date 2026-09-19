"""练习：实现拒绝未知名称和重复注册的工具注册表。"""

from collections.abc import Callable, Mapping

ToolHandler = Callable[[Mapping[str, object]], object]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        # TODO：拒绝空名称和重复名称，再保存处理器。
        raise NotImplementedError("请完成 CH15-EX01")

    def execute(self, name: str, arguments: Mapping[str, object]) -> object:
        # TODO：只执行已经注册的名称，未知名称抛出带工具名的 KeyError。
        raise NotImplementedError("请完成 CH15-EX01")
