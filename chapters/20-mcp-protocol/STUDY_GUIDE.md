# 第 20 章学案：MCP 子进程通信

配合[本章讲解](README.md)使用，画出 client、stdio、server 三段路径。

## MCP 是什么

MCP（Model Context Protocol）约定应用如何与外部能力服务交换信息。服务端可暴露工具、资源和提示模板；客户端发现能力并发起调用。本章只实现工具调用。模型生成工具调用建议与 MCP 传输不是同一件事：前者是模型输出动作，后者是应用访问工具服务的协议，两者可以组合。[协议概览](https://modelcontextprotocol.io/specification/2025-06-18/server/index)。

## 技术栈与落地场景

本项目使用锁定版本的 MCP Python SDK v2、`MCPServer`、`Client`、stdio 子进程和 Pydantic 结构。适用于把工单查询、内部知识检索或开发工具作为独立能力供多个 Agent 客户端使用。stdio 适合本地进程；远程服务还需要真实身份验证、授权、网络运维和租户隔离，本章没有实现这些。

工具描述和 `readOnlyHint` 帮助调用方理解能力，但不能作为权限保证。服务端必须自行检查调用者和资源归属；客户端仍要校验返回结果、处理 `is_error` 和连接失败。stdout 用于协议流，调试日志写 stderr，避免污染消息格式。

## 代码怎样工作

[服务端](../../agent_lab/mcp_server.py)注册查询合成工单的工具；[客户端](../../agent_lab/mcp_demo.py)启动 server 子进程，初始化会话、发现工具、调用并解析结构化结果，退出时关闭连接。[测试](../../tests/test_mcp.py)使用真实子进程验证这条路径。[练习](exercises/exercise_ch20.py)操作的是协议 JSON 字典，因此字段名与 SDK Python 对象的 snake_case 属性可能不同。

## 课前热身

- 第 15 章的本地工具注册表与跨进程工具调用分别解决什么问题？
- 若 server 往 stdout 打印调试文字，stdio 协议会受到什么影响？

## 探究任务

1. 阅读[服务端](../../agent_lab/mcp_server.py)与[客户端](../../agent_lab/mcp_demo.py)，写出启动、工具发现、调用、解析、关闭五步：________。
2. 运行 `python -m tools.run_example --chapter 20`，记录已有工单状态与缺失工单结果：________。
3. 找出 SDK 对象的 snake_case 字段与协议 JSON 的驼峰字段各在哪里使用：________。解释 `readOnlyHint` 为何不能替代权限检查：________。

## 动手完成

- 完成[练习](exercises/exercise_ch20.py)中的协议 JSON 校验，分别测试明确 `isError=false`、错误标志、缺字段、非法状态。
- 运行 `python -m tools.check_exercise --chapter 20`。记录哪条输入被拒绝及原因：________。

## 过关自检

- 能解释工具发现和调用与服务端资源授权的区别。
- 能指出 stdio server 的 stdout 与 stderr 各自用途。
- 能说明如何限制子进程生命周期和调用超时。完成后再看[参考答案](../../solutions/ch20_mcp_protocol.py)。
