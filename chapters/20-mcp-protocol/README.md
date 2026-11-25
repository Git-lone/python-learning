# 第 20 章：MCP 真实进程通信

先修：第 8、10、15、19 章。

### 学习目标

启动真实 MCP server 子进程，发现工具 schema，执行查询并校验结构化结果。把“工具业务失败”和“协议/连接失败”分开理解。

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 跨进程暴露并发现结构化工具接口。
- 权限在服务端执行，业务结果另外做 schema 校验。
- 完成“校验工具返回值而不是只判断 HTTP 成功”并解释失败测试的意义。

## Java 对照

### MCP 真实进程通信 {#compare-mcp-protocol}

- 共同用途：跨进程暴露并发现结构化工具接口。
- 可验证行为差异：本章 Python 使用 MCPServer/Client，底层不是直接调用 Python 函数。
- Python 适用场景：在本地 stdio 子进程中测试 MCP 协议。
- Java 开发者常见误区：将工具说明或 readOnlyHint 当成权限保障。
- 修正方式：权限在服务端执行，业务结果另外做 schema 校验。



MCP 是客户端与服务端的协议，不是 Python 函数装饰器的别名。可以类比 RPC 的接口发现、请求和响应，但工具描述面向模型选择使用。Function calling 是模型输出工具请求的机制；MCP 可以承载工具发现和执行，两者可以组合，并非互斥方案。

## Python 知识

### 代码路径

这里的 **stdio** 是标准输入和标准输出。用 Java 的 `ProcessBuilder` 作类比：父进程向子进程的标准输入写请求，从子进程的标准输出读回复。管道只搬运字节；MCP 另行约定怎样列出工具、传参数和表示错误。本章没有 HTTP 端口，也没有模型参与，是真实的本地跨进程调用。

用工单查两次，就能分清“接口长什么样”和“这次业务是否成功”：

1. `list_tools()` 返回工具说明与 **schema**（数据形状约定）。这里 `ticket_status` 接受字符串 `ticket_id`，类似 Java 请求 DTO 的字段定义。参数类型正确不等于这个工单存在，也不代表有权访问。
2. 给 `call_tool` 传 `{"ticket_id": "DEMO-1"}`，客户端先检查 `is_error`，再让 `Ticket.model_validate` 读取结构化结果，拿到 `waiting_for_customer`。
3. 只把编号改成 `MISSING`：参数仍合法、进程仍能通信，服务端却查无此单，结果中 `is_error` 为真。若子进程压根没启动，则连这样的业务结果都收不到——应排查连接，而不是让用户换一个工单号。

- [mcp_server.py](../../agent_lab/mcp_server.py)：用 MCP Python SDK v2 的 `MCPServer` 注册只读合成工单查询，Pydantic 生成并校验输出结构。
- [mcp_demo.py](../../agent_lab/mcp_demo.py)：`StdioServerParameters` 启动当前虚拟环境 Python；`Client` 管理会话生命周期；发现工具后调用，使用 `is_error` 和 `structured_content` 校验结果。
- [test_mcp.py](../../tests/test_mcp.py)：在真实子进程里跑整个链路，设超时，退出时回收连接和子进程。

本项目固定 `mcp==2.2.0`。旧教程常写 `FastMCP` 和驼峰属性；这里使用 v2 的 `MCPServer` 和 snake_case Python 字段。协议 JSON 仍可能使用 `isError`、`structuredContent` 等序列化字段名，不要混用。

### 教案：走通一次真实 MCP 进程通信（建议 40 分钟）

1. **先画两端（5 分钟）：** 分出 client 进程、server 进程和 stdio 通道。预测 server 在 stdout 随手 `print("debug")` 会怎样影响协议消息。
2. **沿链路读代码（10 分钟）：** 从 `StdioServerParameters` 启动当前 Python，到发现工具、传参调用、解析 `structured_content`。区分工具声明的只读提示与实际服务端授权。
3. **运行观察（10 分钟）：** 运行本章示例，核对已有工单状态和缺失工单的错误路径；确认子进程关闭后不留后台服务。对比 SDK 的 snake_case 属性与协议 JSON 的驼峰字段。
4. **练习（10 分钟）：** 对 `isError=false`、`isError=true`、缺字段和非法状态各写预期，再实现 JSON 合同校验。自测：模型指定任意工单 ID 是否意味着它有读取权限？不意味着；真实系统必须在 server 端验证身份和资源归属。
5. **复盘（5 分钟）：** 用一句话说明 MCP 解决了什么：客户端与工具服务的能力发现和调用协议；业务权限仍由服务端实现。

## 可运行示例

### 运行记录：ch20-demo

```powershell
python -m tools.run_example --chapter 20
python -m pytest tests/test_mcp.py -q
```

应看到 `status=waiting_for_customer` 和 `missing_ticket=handled`。stderr 可包含工具错误日志；stdout 属于 MCP 传输，server 内不要随手 `print` 调试信息。

## 练习

[exercise_ch20.py](exercises/exercise_ch20.py) 接收协议 JSON 字典，只有明确 `isError=false`、工单 ID 为 `DEMO-1`、状态合法时才返回状态；其余情况抛 `ValueError`。这与直接读取 SDK 对象的 snake_case 属性不同。

```powershell
python -m tools.check_exercise --chapter 20
python -m tools.check_exercise --chapter 20 --solution
```

[参考答案](../../solutions/ch20_mcp_protocol.py)。拓展：给工具增加输入长度限制，并增加“字段类型合法但业务资源不属于调用者”的测试。

### 面试时说明边界

- 当前工具仅有 `DEMO-1` 合成数据，不接公司数据库，也没有实现远程鉴权。
- 工具的只读标记是提示信息，不是权限控制。真实系统需服务端身份验证、租户隔离和最小授权。
- 不执行从模型输出中拼接的 shell 命令；远程工具地址、资源范围也要受控。
- 大量工具时，先按身份/场景缩小可用集，再选择或检索工具；不要将所有工具的长描述无限塞进上下文。

来源：[MCP 官方 Python SDK](https://github.com/modelcontextprotocol/python-sdk)、[MCP Server 开发文档](https://modelcontextprotocol.io/docs/develop/build-server)。本章不等于已掌握所有 MCP 传输、授权或扩展特性。

## 验证方式

运行 `python -m tools.check_exercise --chapter 20` 验证自己的实现，`--solution` 用于核对参考答案。示例合同由 `python -m tools.run_example --chapter 20` 验证；工程异常测试见根目录 tests。

## 章节总结

权限在服务端执行，业务结果另外做 schema 校验。面试时同时说明实现、测试证据和未实现边界；公开原帖与自编练习分别见 [真实面经](../../career/INTERVIEW_EXPERIENCES.md) 和 [面试练习](../../career/INTERVIEW_PRACTICE.md)。
