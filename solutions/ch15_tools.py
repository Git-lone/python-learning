"""CH15-EX01 参考答案：将工具名称映射到应用明确注册的处理函数。

注册表只负责查找与分发；参数 Schema、用户权限和执行超时需要由
调用层或具体处理器承担，不能把“已经注册”当作业务授权已经通过。
"""

from collections.abc import Callable, Mapping

ToolHandler = Callable[[Mapping[str, object]], object]


class ToolRegistry:
    """保存名称到处理器的映射，类似 Java 中持有函数接口实例的 Map。

    Python 函数可以直接作为值存储，无需为每个工具创建一个实现类。
    Mapping 描述只读访问接口，但不会把传入的可变字典自动冻结。
    """

    def __init__(self) -> None:
        """为每个注册表实例创建独立的工具集合，避免实例间共享可变状态。"""
        self._tools: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        """登记一个非空且未占用的名称；重复注册时拒绝覆盖已有处理器。"""
        # 工具集合在应用启动时确定，模型无权动态添加新处理器。
        if not name.strip():
            raise ValueError("tool name must not be empty")
        if name in self._tools:
            raise ValueError(f"duplicate tool: {name}")
        self._tools[name] = handler

    def execute(self, name: str, arguments: Mapping[str, object]) -> object:
        """将参数交给指定工具并返回其结果；未知名称与业务异常都向外抛出。"""
        try:
            handler = self._tools[name]
        except KeyError as error:
            # 保留原 KeyError 作为原因，同时提供可审计的工具名称。
            raise KeyError(f"unknown tool: {name}") from error
        # 只捕获查找失败，不吞掉 handler 的业务异常；重试策略由调用层决定。
        return handler(arguments)
