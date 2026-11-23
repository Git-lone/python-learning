"""第 20 章 MCP 服务端：把只读的模拟工单查询注册为可发现、可调用的工具。

MCP 在此负责工具契约与进程间通信，不负责模型如何选择工具。客户端会另启进程
运行本模块，stdout 专用于协议传输；本例不连接真实工单系统或客户数据。
"""

from mcp.server import MCPServer
from pydantic import BaseModel, ConfigDict

server = MCPServer("ticket-lab")


# 工具结果的结构化契约；Pydantic 模型既参与结果校验，也参与对外 Schema 生成。
# 类说明使用普通注释，避免新增 docstring 被框架转为 Schema 的 description。
class Ticket(BaseModel):
    # Pydantic 执行运行时校验；extra=forbid 拒绝契约外字段，与普通类型提示不同。
    model_config = ConfigDict(extra="forbid")
    ticket_id: str
    status: str


# 注册函数签名、说明和返回模型，供客户端发现工具及其参数/结果 Schema。
# 函数 docstring 会成为对外工具描述，因此保留原文；下方分支只模拟存在/不存在两种结果。
@server.tool()
def ticket_status(ticket_id: str) -> Ticket:
    """Read status of a synthetic ticket. Only DEMO-1 exists; no customer data."""
    # 业务异常由 MCP 框架包装为工具错误；客户端仍需检查结果中的 is_error。
    if ticket_id != "DEMO-1":
        raise ValueError("ticket not found")
    return Ticket(ticket_id=ticket_id, status="waiting_for_customer")


if __name__ == "__main__":
    # stdio 的 stdout 属于协议通道，调试日志应写 stderr，不能随意 print 污染消息。
    server.run(transport="stdio")
