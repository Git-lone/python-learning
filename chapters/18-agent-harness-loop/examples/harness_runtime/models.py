"""Harness 运行时使用的领域数据结构，顶层字段采用不可变设计。

dataclass 类似 Java record，便于将动作、观察和运行快照分开表达。
frozen 防止重新给字段赋值，slots 限制动态添加字段；二者都不自动冻结嵌套字典。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ToolCall:
    """模型提出的工具调用；call_id 同时充当幂等键。"""

    # 这里只携带幂等标识；是否防重、是否校验同键不同参数，必须由执行工具实现。
    call_id: str
    name: str
    # Mapping 是只读接口提示，frozen 也只限制字段赋值；嵌套字典没有被深度冻结。
    arguments: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FinalAnswer:
    """模型建议结束当前循环时给出的答案。"""

    text: str


@dataclass(frozen=True, slots=True)
class ToolObservation:
    """工具成功、拒绝或失败后反馈给模型的确定性观察。"""

    call_id: str
    name: str
    result: object
    error: str | None = None


@dataclass(frozen=True, slots=True)
class VerificationObservation:
    """完成条件未满足时反馈给模型的修正信息。"""

    feedback: str


Action = ToolCall | FinalAnswer
HistoryEvent = ToolCall | ToolObservation | VerificationObservation
# Literal 辅助静态检查，合法状态迁移仍必须由运行时代码保证。
RunStatus = Literal["running", "waiting_approval", "completed", "failed"]


@dataclass(frozen=True, slots=True)
class HarnessLimits:
    """Harness 强制执行的模型轮数和工具调用双重预算。"""

    # 两者都是次数上限，不限制单次调用耗时、输入 token 数或真实模型账单金额。
    max_steps: int = 6
    max_tool_calls: int = 3

    def __post_init__(self) -> None:
        """在 dataclass 自动生成的初始化之后校验数值下限，尽早暴露错误配置。"""

        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        if self.max_tool_calls < 1:
            raise ValueError("max_tool_calls must be positive")


@dataclass(frozen=True, slots=True)
class RunState:
    """记录恢复循环需要的目标、轨迹、计数和未完成动作。

    状态通过 replace 推进，类似 Java 中从旧 record 构造新 record。
    工具注册、预算配置和审批身份不在本快照里；示例恢复时使用当前 Harness 的配置。
    """

    run_id: str
    objective: str
    status: RunStatus = "running"
    # step 统计模型决策，tool_calls 统计真正进入处理器的尝试，两种预算不能混用。
    step: int = 0
    tool_calls: int = 0
    history: tuple[HistoryEvent, ...] = ()
    # 已有决策但尚未完成的工具调用；恢复时优先处理它，避免再次让模型生成动作。
    pending_call: ToolCall | None = None
    answer: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class RunEvent:
    """供日志、指标或 Trace 适配器消费的事件，detail 应由调用方提供脱敏内容。

    这个数据类不自动清洗文本；自定义验收反馈和失败原因仍需调用方检查。
    """

    run_id: str
    kind: str
    step: int
    detail: str
