import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from agent_lab.mcp_server import Ticket


async def demo() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "agent_lab.mcp_server"],
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    async with asyncio.timeout(20):
        async with Client(params, read_timeout_seconds=10) as client:
            listing = await client.list_tools()
            tool = next(tool for tool in listing.tools if tool.name == "ticket_status")
            assert "ticket_id" in tool.input_schema["properties"]
            result = await client.call_tool("ticket_status", {"ticket_id": "DEMO-1"})
            if result.is_error:
                raise RuntimeError("tool returned an error")
            ticket = Ticket.model_validate(result.structured_content)
            print(f"MCP tool={tool.name} status={ticket.status}")
            missing = await client.call_tool("ticket_status", {"ticket_id": "MISSING"})
            assert missing.is_error
            print("MCP missing_ticket=handled")


if __name__ == "__main__":
    asyncio.run(demo())
