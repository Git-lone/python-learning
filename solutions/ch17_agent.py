"""CH17-EX01 参考答案：用显式事件和步数预算实现最小 Agent 循环。

模型负责提出工具调用或最终答案，执行器负责工具白名单、执行和结果回传。
模型由调用者注入，可以是预设动作的假模型；本模块没有接入真实模型服务。
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ToolCall:
    """一次待执行的工具请求；名称和参数仍需经过执行边界的检查。"""

    name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FinalAnswer:
    """模型主动结束本轮任务时返回的答案，与工具请求形成两种动作。"""

    text: str


@dataclass(frozen=True, slots=True)
class ToolObservation:
    """执行器反馈的成功结果或错误，供模型下一步决策使用。"""

    name: str
    result: object
    error: str | None = None


Action = ToolCall | FinalAnswer
Event = ToolCall | ToolObservation
ToolHandler = Callable[[Mapping[str, object]], object]


class AgentModel(Protocol):
    """声明模型适配器所需的方法，不限定其 SDK 或内部实现。

    Protocol 使用结构化类型：对象提供匹配的方法即可参与静态类型检查，
    不必像常见 Java 接口用法那样显式声明 implements；运行时不自动校验返回值。
    """

    def next_action(self, history: Sequence[Event]) -> Action: ...


@dataclass(frozen=True, slots=True)
class AgentResult:
    """返回最终答案、工具交互历史和已消耗决策步数；最终答案不加入历史。"""

    answer: str
    history: tuple[Event, ...]
    steps: int


class StepLimitError(RuntimeError):
    """Agent 未在预算内结束。"""


def run_agent(
    model: AgentModel, tools: Mapping[str, ToolHandler], max_steps: int = 4
) -> AgentResult:
    """推进模型决策与工具执行，获得最终答案后返回结果，耗尽预算则抛错。

    工具异常会转为观察供模型处理，模型适配器本身的异常则直接传播。
    max_steps 限制决策次数，不限制单次模型或工具调用耗时；本练习也没有
    持久化、参数 Schema 校验或写操作审批，不能直接当作完整生产运行时。
    """
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    history: list[Event] = []
    # 预算按模型决策计数，最终答案也占一步，工具错误后继续同样会消耗剩余预算。
    for step in range(1, max_steps + 1):
        # tuple 限制历史序列的增删，不会冻结事件中的嵌套参数对象。
        action = model.next_action(tuple(history))
        if isinstance(action, FinalAnswer):
            return AgentResult(action.text, tuple(history), step)
        # 先记录请求再记录结果，保留“决定调用什么—实际发生什么”的对应关系。
        history.append(action)
        handler = tools.get(action.name)
        if handler is None:
            # 白名单之外的名称永不执行，只形成可见的拒绝观察。
            history.append(ToolObservation(action.name, None, "tool not allowed"))
            continue
        try:
            result = handler(action.arguments)
        except Exception as error:
            # 教学版保留简短消息；生产版应映射稳定错误码并清理敏感信息。
            history.append(ToolObservation(action.name, None, str(error)))
        else:
            history.append(ToolObservation(action.name, result))
    # 步数预算是 Agent 最基本的失控保护。
    raise StepLimitError(f"agent exceeded {max_steps} steps")
