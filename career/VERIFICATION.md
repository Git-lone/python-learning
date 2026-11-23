# 本次验证记录

2026-11-23 在 Windows 和 Python 3.13.15 的项目虚拟环境中验证，依赖版本见 [requirements-dev.lock](../requirements-dev.lock)。以下命令均在仓库根目录执行。

| 检查 | 结果 |
|---|---|
| `python -m tools.run_example --all` | 24 章共 25 个示例通过，含第 15 章的六组工具输入与第 18 章的两条审批路径 |
| `python -m tools.check_exercise --all --solution` | 24/24 章参考答案验收通过 |
| `python -m pytest -q` | 65 项测试通过，包括章节标题与目录对应、示例输出展示、工具分派边界和工作流状态查询 |
| `python -m mypy` | 17 个源文件通过，范围为 agent_lab 与 tools |
| `python -m tools.validate_content` | 原有严格文档、清单与导航校验通过 |
| `python -m tools.validate_links` | 含 career 文档的补充链接校验通过 |
| `python -m ruff check .` | 仓库代码检查通过 |
| `python -m pip check` | 未发现损坏依赖 |

pytest 报告了 1 条依赖弃用提示，来自 Starlette TestClient 对 AnyIO 别名的使用。

真实执行了 MCP stdio 子进程，以及 LangGraph 审批前退出、另一个进程恢复的示例。OpenAI SDK 使用 HTTPX2 mock transport 验证事件解析，没有发送真实付费模型请求；API 使用本地 TestClient 验证，没有声称已经做完生产部署或网络压测。

尚未验证：Python 3.12、macOS/Linux、远端模型质量、真实费用、生产认证、真实外部副作用、分布式并发恢复、网络代理层断连/背压。空白练习保留为学习任务，并非全部填写完毕。
