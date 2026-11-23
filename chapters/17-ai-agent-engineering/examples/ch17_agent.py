"""一个最小但完整的 Agent 循环：决策、工具、观察、结束。

先读动作与观察类型，再跟随 run_agent，最后看 DemoModel 如何利用上一条观察。
循环不依赖具体 SDK；本章把状态保存在内存，第 18 章再引入审批、检查点与完成验收。
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ToolCall:
    """模型提出的执行请求，类似带参数的命令对象；创建它并不会立即调用工具。"""

    name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FinalAnswer:
    """表示模型选择结束；与 ToolCall 分开建模，避免靠特殊文本判断控制流程。"""

    text: str


@dataclass(frozen=True, slots=True)
class ToolObservation:
    """记录确定性执行结果或错误，作为下一次模型决策的输入。"""

    name: str
    result: object
    error: str | None = None


Action = ToolCall | FinalAnswer
Event = ToolCall | ToolObservation
# 联合类型类似 Java sealed interface 的备选实现，帮助区分决策和执行反馈。
ToolHandler = Callable[[Mapping[str, object]], object]


class AgentModel(Protocol):
    """定义一步决策能力；模型可替换，历史维护和实际执行仍由循环控制。"""

    def next_action(self, history: Sequence[Event]) -> Action:
        """读取已有调用与观察，返回下一次工具请求或最终答案。"""

        ...


@dataclass(frozen=True, slots=True)
class AgentResult:
    """把最终回答、完整工具轨迹和决策次数一起交回调用方，便于解释与验证。"""

    answer: str
    history: tuple[Event, ...]
    steps: int


class StepLimitError(RuntimeError):
    """Agent 未在预算内结束。"""


def run_agent(
    model: AgentModel, tools: Mapping[str, ToolHandler], max_steps: int = 4
) -> AgentResult:
    """在决策预算内反复执行“模型动作 → 工具观察”，直到模型给出最终答案。

    工具失败会变成观察供模型修正；模型调用本身的异常直接向上抛出。
    这里依赖模型遵守 Action 类型约定，也未限制单次调用耗时或检查最终答案是否正确。
    """

    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    history: list[Event] = []
    # 一步指一次模型决策，返回最终答案也占一步，不等于工具调用次数。
    for step in range(1, max_steps + 1):
        # 模型只能提出动作；循环仍由确定性代码掌握控制权。
        # tuple 防止模型增删这份历史序列，但 arguments 等嵌套对象并未深度冻结。
        action = model.next_action(tuple(history))
        if isinstance(action, FinalAnswer):
            return AgentResult(action.text, tuple(history), step)
        history.append(action)
        handler = tools.get(action.name)
        if handler is None:
            # 未知工具作为观察返回，绝不能退化为反射、eval 或 shell 执行。
            history.append(ToolObservation(action.name, None, "tool not allowed"))
            continue
        try:
            result = handler(action.arguments)
        except Exception as error:
            # 工具错误进入轨迹，模型下一步可以选择修正参数或结束。
            # 教学示例直接记录异常文本；接入真实服务前需对错误信息脱敏。
            history.append(ToolObservation(action.name, None, str(error)))
        else:
            history.append(ToolObservation(action.name, result))
    # 硬上限保证错误模型不会造成无限工具调用和费用增长。
    raise StepLimitError(f"agent exceeded {max_steps} steps")


class DemoModel:
    """固定两步策略：先请求加法，再读取观察生成回答，用于看清循环如何推进。"""

    def next_action(self, history: Sequence[Event]) -> Action:
        """首次调用不依赖历史；第二次利用运行器追加的工具结果。"""

        if not history:
            return ToolCall("add", {"left": 2, "right": 3})
        observation = history[-1]
        assert isinstance(observation, ToolObservation)
        # 演示模型只覆盖成功路径；真实决策还应处理 observation.error，避免把失败当答案。
        return FinalAnswer(f"2 + 3 = {observation.result}")


def add(arguments: Mapping[str, object]) -> int:
    """供循环执行的确定性函数；工具接收动态参数，自行承担输入检查。"""

    # 此处简化校验会接受 bool，因为 bool 是 int 子类；严格版本见 CH15 的 add。
    left = arguments.get("left")
    right = arguments.get("right")
    if not isinstance(left, int) or not isinstance(right, int):
        raise ValueError("integer arguments required")
    return left + right


def main() -> int:
    """运行两步离线 Agent，并展示工具观察如何进入最终回答。"""

    result = run_agent(DemoModel(), {"add": add})
    observation = result.history[-1]
    assert isinstance(observation, ToolObservation)
    print(f"tool={observation.name} result={observation.result}")
    print(f"final={result.answer} steps={result.steps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
