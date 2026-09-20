"""CH15-EX01 参考答案。"""

from collections.abc import Callable, Mapping

ToolHandler = Callable[[Mapping[str, object]], object]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        # 工具集合在应用启动时确定，模型无权动态添加新处理器。
        if not name.strip():
            raise ValueError("tool name must not be empty")
        if name in self._tools:
            raise ValueError(f"duplicate tool: {name}")
        self._tools[name] = handler

    def execute(self, name: str, arguments: Mapping[str, object]) -> object:
        try:
            handler = self._tools[name]
        except KeyError as error:
            # 保留原 KeyError 作为原因，同时提供可审计的工具名称。
            raise KeyError(f"unknown tool: {name}") from error
        # 只捕获查找失败，不吞掉 handler 的业务异常；重试策略由调用层决定。
        return handler(arguments)
