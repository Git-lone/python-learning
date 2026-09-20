import asyncio
from agent_lab.mcp_demo import demo

if __name__ == "__main__":
    # 会启动真实 MCP stdio 子进程并发现、调用工具，但工具数据完全是本地模拟数据。
    asyncio.run(demo())
