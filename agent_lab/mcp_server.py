"""Read-only, synthetic ticket tool. Stdout is reserved for MCP transport."""

from mcp.server import MCPServer
from pydantic import BaseModel, ConfigDict

server = MCPServer("ticket-lab")


class Ticket(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: str
    status: str


@server.tool()
def ticket_status(ticket_id: str) -> Ticket:
    """Read status of a synthetic ticket. Only DEMO-1 exists; no customer data."""
    if ticket_id != "DEMO-1":
        raise ValueError("ticket not found")
    return Ticket(ticket_id=ticket_id, status="waiting_for_customer")


if __name__ == "__main__":
    server.run(transport="stdio")
