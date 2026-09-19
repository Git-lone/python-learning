# 本次验证记录

日期：2026-09-19。环境：Windows，Python 3.13.15，项目根目录 `C:\workspace\my\py\learning`。依赖见 pyproject 与 requirements-dev.lock。

| 检查 | 结果 |
|---|---|
| `python -m tools.run_example --all` | 24/24 个示例通过 |
| `python -m tools.check_exercise --all --solution` | 24/24 章参考答案验收通过 |
| `python -m pytest -q` | 51 项测试通过 |
| `python -m mypy` | 17 个源文件通过，范围为 agent_lab 与 tools |
| `python -m tools.validate_content` | 原有严格文档、清单与导航校验通过 |
| `python -m tools.validate_links` | 含 career 文档的补充链接校验通过 |
| Ruff | 新增实战代码、练习与答案，以及 tools/tests 检查通过 |
| `python -m pip check` | 未发现损坏依赖 |

Ruff 检查范围为 agent_lab、tools、tests、第 19～24 章目录以及 ch19～ch24 参考答案；未对旧章节做格式化重写。pytest 有 1 条来自 Starlette TestClient 使用 AnyIO 弃用别名的 DeprecationWarning，不影响本次通过结果；没有屏蔽该提示。

真实执行了 MCP stdio 子进程，以及 LangGraph 审批前退出、另一个进程恢复的示例。OpenAI SDK 使用 HTTPX2 mock transport 验证事件解析，没有发送真实付费模型请求；API 使用本地 TestClient 验证，没有声称已经做完生产部署或网络压测。

尚未验证：Python 3.12、macOS/Linux、远端模型质量、真实费用、生产认证、真实外部副作用、分布式并发恢复、网络代理层断连/背压。空白练习保留为学习任务，并非全部填写完毕。
