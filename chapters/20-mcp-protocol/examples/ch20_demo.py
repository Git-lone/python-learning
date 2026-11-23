"""第 20 章最小演示：通过 MCP 协议发现工具，调用工单查询并检查错误结果。

依次跟读 agent_lab.mcp_demo 的客户端流程和 mcp_server 的工具定义，区分
“协议连接正常”与“业务查询成功”。本例没有让 LLM 自动挑选工具或编排任务。
"""

import asyncio
from agent_lab.mcp_demo import demo

if __name__ == "__main__":
    # 会启动真实 MCP stdio 子进程并发现、调用工具，但工具数据完全是本地模拟数据。
    asyncio.run(demo())
