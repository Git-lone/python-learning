"""离线 Agent Harness 教学包的公共 API。

models 定义数据，ports 定义协作合同，runtime 推进状态，adapters 提供离线实现。
这里集中导出示例需要的名称，使调用方无需了解内部文件如何拆分。
"""

from .adapters import ListEventSink, MemoryCheckpointStore
from .models import (
    Action,
    FinalAnswer,
    HarnessLimits,
    HistoryEvent,
    RunEvent,
    RunState,
    ToolCall,
    ToolObservation,
    VerificationObservation,
)
from .ports import AgentModel, CompletionVerifier, ToolHandler, ToolSpec
from .runtime import AgentHarness

__all__ = [
    "Action",
    "AgentHarness",
    "AgentModel",
    "CompletionVerifier",
    "FinalAnswer",
    "HarnessLimits",
    "HistoryEvent",
    "ListEventSink",
    "MemoryCheckpointStore",
    "RunEvent",
    "RunState",
    "ToolCall",
    "ToolHandler",
    "ToolObservation",
    "ToolSpec",
    "VerificationObservation",
]
