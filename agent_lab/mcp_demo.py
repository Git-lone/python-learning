import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from agent_lab.mcp_server import Ticket


async def demo() -> None:
    # 使用当前虚拟环境的解释器启动子进程，避免系统 Python 缺少 MCP 依赖。
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "agent_lab.mcp_server"],
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    # 外层限制完整演示时长；Client 上下文负责会话及子进程的资源回收。
    async with asyncio.timeout(20):
        async with Client(params, read_timeout_seconds=10) as client:
            # 先发现工具并检查 Schema，再调用；名称存在不代表参数契约正确。
            listing = await client.list_tools()
            tool = next(tool for tool in listing.tools if tool.name == "ticket_status")
            assert "ticket_id" in tool.input_schema["properties"]
            result = await client.call_tool("ticket_status", {"ticket_id": "DEMO-1"})
            # 协议请求成功和业务工具成功要分开判断，再校验结构化结果。
            if result.is_error:
                raise RuntimeError("tool returned an error")
            ticket = Ticket.model_validate(result.structured_content)
            print(f"MCP tool={tool.name} status={ticket.status}")
            missing = await client.call_tool("ticket_status", {"ticket_id": "MISSING"})
            assert missing.is_error
            print("MCP missing_ticket=handled")


if __name__ == "__main__":
    asyncio.run(demo())
