"""Read-only, synthetic ticket tool. Stdout is reserved for MCP transport."""

from mcp.server import MCPServer
from pydantic import BaseModel, ConfigDict

server = MCPServer("ticket-lab")


class Ticket(BaseModel):
    # Pydantic 执行运行时校验；extra=forbid 拒绝契约外字段，与普通类型提示不同。
    model_config = ConfigDict(extra="forbid")
    ticket_id: str
    status: str


# 注册函数签名、说明和返回模型，供客户端发现工具及其参数/结果 Schema。
@server.tool()
def ticket_status(ticket_id: str) -> Ticket:
    """Read status of a synthetic ticket. Only DEMO-1 exists; no customer data."""
    if ticket_id != "DEMO-1":
        raise ValueError("ticket not found")
    return Ticket(ticket_id=ticket_id, status="waiting_for_customer")


if __name__ == "__main__":
    # stdio 的 stdout 属于协议通道，调试日志应写 stderr，不能随意 print 污染消息。
    server.run(transport="stdio")
