# 技术资料与版本记录

核查日期：2026-09-19。厂商与框架文档用于技术合同核对；面经只用于了解公开自述的考察问题，二者不互相替代。

| 资料 | 本教程使用位置 |
|---|---|
| [OpenAI Python SDK](https://github.com/openai/openai-python) | 异步客户端、Responses API、HTTP transport 和资源关闭 |
| [OpenAI Streaming Responses](https://developers.openai.com/api/docs/guides/streaming-responses) | delta、完成与失败事件 |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | v2 MCPServer、Client、stdio 通信 |
| [MCP Server 开发文档](https://modelcontextprotocol.io/docs/develop/build-server) | 工具服务与传输基本概念 |
| [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) | 暂停、同 thread 恢复、节点重执行 |
| [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | checkpointer 与 SQLite 本地持久化 |
| [FastAPI 自定义响应](https://fastapi.tiangolo.com/advanced/custom-response/) | StreamingResponse |
| [rank_bm25](https://github.com/dorianbrown/rank_bm25) | 现成 BM25 实现，分词由调用方负责 |

实际测试环境是 Windows、Python 3.13.15。`pyproject.toml` 约束 Python >=3.12,<3.14，3.12 尚未单独跑过本次测试；不要把声明支持范围等同于已测版本矩阵。

直接依赖已固定版本，`requirements-dev.lock` 是此次 Windows 环境解析出的完整 pip freeze 快照，不是带哈希的供应链锁文件，也不是跨平台通用锁。换平台使用 pyproject 安装并重新验证；升级 SDK 时先看迁移说明，再跑完整示例与验收。

当前 MCP 2.x 与旧的 1.x 教程代码有差异，OpenAI SDK 3.x 的默认 HTTP 客户端也与一些旧示例不同。新代码依据已安装版本及官方文档编写，不保证复制旧博客片段可直接工作。
