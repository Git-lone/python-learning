# Python 与 Agent 开发求职教程

这是一门给 Java 后端开发者的 Python 与 Agent 应用开发课。从 Python 基础开始，可以一路做到带工具、审批和持久化的应用。下文的命令都在含有 `pyproject.toml` 和 `catalog.toml` 的仓库根目录运行。

保留 Python 基础与教学 Agent Loop，新增模型 SDK、MCP、LangGraph 持久化、检索评测和 API 服务，共 **24 章**。默认全程使用合成数据和离线模型 fixture，只有显式 --live 才访问可能计费的模型 API。

## 先从这里开始

- [按能力安排的学习路线](career/ROADMAP.md)
- [AI 求职：完整功能实现与项目经历详解（可直接转交其他 AI）](career/project-experience/AI应用项目_实现机制与项目经历详解.md)
- [AI 应用开发：近期项目经历与技术亮点](career/project-experience/AI应用开发_项目经历精炼.md)
- [真实面经原帖、日期与题目映射](career/INTERVIEW_EXPERIENCES.md)
- [技术追问、系统设计与模拟面试](career/INTERVIEW_PRACTICE.md)
- [作品集与诚实的简历表述](career/PORTFOLIO.md)
- [官方资料与版本说明](career/REFERENCES.md)
- [本次验证记录与未测范围](career/VERIFICATION.md)
- [章节索引](INDEX.md)

刚接触 Python，可以从[第 1 章](chapters/01-basics/README.md)开始。每章先填学案里的预测，再运行示例、对照输出，最后用练习检查自己能否独立实现。章节写作约定见[课程写作基准](COURSE_DESIGN.md)。

熟悉 Python、想先体验业务 Agent，可以按下面的顺序做实验。

| 要解决的问题 | 动手做什么 |
|---|---|
| 模型能读懂退款诉求吗？ | 用四条消息找出关键词分类器的误判和漏判。[第 14 章 · LLM 应用](chapters/14-llm-application-basics/README.md) |
| 模型提出的动作能执行吗？ | 给工具注册表输入合法调用、错误参数和未知工具名，记录每种输入在哪一步得到处理。[第 15 章 · 工具调用](chapters/15-structured-output-tools/README.md) |
| 工具结果如何影响下一步？ | 数一遍模型决策和工具执行次数，再观察人工批准或拒绝后运行如何收尾。[第 17 章 · Agent Loop](chapters/17-ai-agent-engineering/README.md) · [第 18 章 · Harness](chapters/18-agent-harness-loop/README.md) |
| 进程退出后，怎样接着上次审批？ | 在另一个进程中恢复同一线程，对照流程检查点与业务账本。[第 21 章 · 持久化实验](chapters/21-durable-workflow/STUDY_GUIDE.md) |

## 安装与运行

首次在 Windows 使用时，在仓库根目录打开 PowerShell，确认 `python --version` 为 3.12 或 3.13，然后执行以下命令。已安装好项目依赖的读者可以直接运行最后一行。

```powershell
$env:PYTHONUTF8 = "1"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock -e ".[dev]"
.\.venv\Scripts\python.exe -m tools.run_example --chapter 17
```

这是 Python 3.13.15 / Windows 验证环境的依赖快照。其他平台优先从 pyproject 安装：`python -m pip install -e ".[dev]"`，然后重跑验证。安装只影响项目 venv，不改系统 Python、Java 或 Maven 配置。

下文与各章中的 `python` 都指本项目虚拟环境。可执行 `.\.venv\Scripts\Activate.ps1` 激活；被执行策略拦截时直接用完整的 `.\.venv\Scripts\python.exe`，无需修改系统执行策略。

上面的第 17 章示例会打印 `tool=add result=5` 和 `final=2 + 3 = 5 steps=2`。一次决策提出加法工具调用，另一次读取结果并给出答案，所以执行一次工具用了两次决策。按章运行时可以直接对照学案观察输出，`--all` 用于批量检查，失败时会展开对应示例的输出。

## 示例、练习、参考答案

```powershell
python -m tools.run_example --all
python -m tools.check_exercise --chapter 21
python -m tools.check_exercise --chapter 21 --solution
python -m tools.check_exercise --all --solution
python -m pytest -q
python -m mypy
python -m tools.validate_content
python -m tools.validate_links
```

练习模板中的 NotImplementedError 是等待你完成的题目，不是运行环境坏了。全量回归对参考答案运行；不要为了得到绿色结果把所有练习改成自动导入答案。pytest 默认跑工程/课程测试与基础综合项目，不自动要求尚未完成的练习通过。

## 课程导航

| 编号 | 主题 | 先修章节 | 唯一入口 |
|---:|---|---|---|
| 1 | 基础语法 | 无 | [进入第 1 章](chapters/01-basics/README.md) |
| 2 | 集合与推导式 | [第 1 章](chapters/01-basics/README.md) | [进入第 2 章](chapters/02-collections-comprehensions/README.md) |
| 3 | 函数与装饰器 | [第 1 章](chapters/01-basics/README.md)、[第 2 章](chapters/02-collections-comprehensions/README.md) | [进入第 3 章](chapters/03-functions-decorators/README.md) |
| 4 | 面向对象与数据类 | [第 1 章](chapters/01-basics/README.md)、[第 3 章](chapters/03-functions-decorators/README.md) | [进入第 4 章](chapters/04-oop-dataclasses/README.md) |
| 5 | 异常处理 | [第 1 章](chapters/01-basics/README.md)、[第 3 章](chapters/03-functions-decorators/README.md) | [进入第 5 章](chapters/05-exceptions/README.md) |
| 6 | 模块与包 | [第 1 章](chapters/01-basics/README.md)、[第 3 章](chapters/03-functions-decorators/README.md) | [进入第 6 章](chapters/06-modules-packages/README.md) |
| 7 | 文件与上下文管理器 | [第 5 章](chapters/05-exceptions/README.md)、[第 6 章](chapters/06-modules-packages/README.md) | [进入第 7 章](chapters/07-files-context-managers/README.md) |
| 8 | 类型提示 | [第 3 章](chapters/03-functions-decorators/README.md)、[第 4 章](chapters/04-oop-dataclasses/README.md)、[第 6 章](chapters/06-modules-packages/README.md) | [进入第 8 章](chapters/08-type-hints/README.md) |
| 9 | 迭代器与生成器 | [第 2 章](chapters/02-collections-comprehensions/README.md)、[第 3 章](chapters/03-functions-decorators/README.md) | [进入第 9 章](chapters/09-iterators-generators/README.md) |
| 10 | 同步并发与异步并发 | [第 3 章](chapters/03-functions-decorators/README.md)、[第 5 章](chapters/05-exceptions/README.md)、[第 9 章](chapters/09-iterators-generators/README.md) | [进入第 10 章](chapters/10-concurrency-asyncio/README.md) |
| 11 | 自动化测试 | [第 3 章](chapters/03-functions-decorators/README.md)、[第 5 章](chapters/05-exceptions/README.md)、[第 6 章](chapters/06-modules-packages/README.md)、[第 8 章](chapters/08-type-hints/README.md) | [进入第 11 章](chapters/11-automated-testing/README.md) |
| 12 | 配置、命令行与日志 | [第 5 章](chapters/05-exceptions/README.md)、[第 6 章](chapters/06-modules-packages/README.md)、[第 8 章](chapters/08-type-hints/README.md)、[第 11 章](chapters/11-automated-testing/README.md) | [进入第 12 章](chapters/12-configuration-cli-logging/README.md) |
| 13 | HTTP API 与可靠性 | [第 5 章](chapters/05-exceptions/README.md)、[第 7 章](chapters/07-files-context-managers/README.md)、[第 8 章](chapters/08-type-hints/README.md)、[第 10 章](chapters/10-concurrency-asyncio/README.md)、[第 12 章](chapters/12-configuration-cli-logging/README.md) | [进入第 13 章](chapters/13-http-api-resilience/README.md) |
| 14 | LLM 应用基础 | [第 4 章](chapters/04-oop-dataclasses/README.md)、[第 5 章](chapters/05-exceptions/README.md)、[第 8 章](chapters/08-type-hints/README.md)、[第 13 章](chapters/13-http-api-resilience/README.md) | [进入第 14 章](chapters/14-llm-application-basics/README.md) |
| 15 | 结构化输出与工具调用 | [第 4 章](chapters/04-oop-dataclasses/README.md)、[第 5 章](chapters/05-exceptions/README.md)、[第 8 章](chapters/08-type-hints/README.md)、[第 14 章](chapters/14-llm-application-basics/README.md) | [进入第 15 章](chapters/15-structured-output-tools/README.md) |
| 16 | 检索增强与对话记忆 | [第 2 章](chapters/02-collections-comprehensions/README.md)、[第 7 章](chapters/07-files-context-managers/README.md)、[第 8 章](chapters/08-type-hints/README.md)、[第 9 章](chapters/09-iterators-generators/README.md)、[第 14 章](chapters/14-llm-application-basics/README.md) | [进入第 16 章](chapters/16-rag-memory/README.md) |
| 17 | AI Agent 工程 | [第 5 章](chapters/05-exceptions/README.md)、[第 10 章](chapters/10-concurrency-asyncio/README.md)、[第 11 章](chapters/11-automated-testing/README.md)、[第 14 章](chapters/14-llm-application-basics/README.md)、[第 15 章](chapters/15-structured-output-tools/README.md)、[第 16 章](chapters/16-rag-memory/README.md) | [进入第 17 章](chapters/17-ai-agent-engineering/README.md) |
| 18 | Agent Harness 与循环工程 | [第 7 章](chapters/07-files-context-managers/README.md)、[第 11 章](chapters/11-automated-testing/README.md)、[第 12 章](chapters/12-configuration-cli-logging/README.md)、[第 17 章](chapters/17-ai-agent-engineering/README.md) | [进入第 18 章](chapters/18-agent-harness-loop/README.md) |
| 19 | 真实模型 SDK 与流式边界 | [第 10 章](chapters/10-concurrency-asyncio/README.md)、[第 13 章](chapters/13-http-api-resilience/README.md)、[第 14 章](chapters/14-llm-application-basics/README.md) | [进入第 19 章](chapters/19-model-sdk/README.md) |
| 20 | MCP 真实进程通信 | [第 8 章](chapters/08-type-hints/README.md)、[第 10 章](chapters/10-concurrency-asyncio/README.md)、[第 15 章](chapters/15-structured-output-tools/README.md)、[第 19 章](chapters/19-model-sdk/README.md) | [进入第 20 章](chapters/20-mcp-protocol/README.md) |
| 21 | LangGraph 持久化与人工审批 | [第 7 章](chapters/07-files-context-managers/README.md)、[第 11 章](chapters/11-automated-testing/README.md)、[第 18 章](chapters/18-agent-harness-loop/README.md)、[第 20 章](chapters/20-mcp-protocol/README.md) | [进入第 21 章](chapters/21-durable-workflow/README.md) |
| 22 | 检索实现与离线评测 | [第 11 章](chapters/11-automated-testing/README.md)、[第 16 章](chapters/16-rag-memory/README.md)、[第 19 章](chapters/19-model-sdk/README.md) | [进入第 22 章](chapters/22-retrieval-evaluation/README.md) |
| 23 | FastAPI 服务与 SSE 协议 | [第 10 章](chapters/10-concurrency-asyncio/README.md)、[第 13 章](chapters/13-http-api-resilience/README.md)、[第 19 章](chapters/19-model-sdk/README.md)、[第 22 章](chapters/22-retrieval-evaluation/README.md) | [进入第 23 章](chapters/23-agent-api/README.md) |
| 24 | 上线指标与作品集验收 | [第 18 章](chapters/18-agent-harness-loop/README.md)、[第 21 章](chapters/21-durable-workflow/README.md)、[第 22 章](chapters/22-retrieval-evaluation/README.md)、[第 23 章](chapters/23-agent-api/README.md) | [进入第 24 章](chapters/24-production-readiness/README.md) |

## 项目地图

- [基础综合项目：任务进度报告器](capstone/README.md)：第 1～11 章实践。
- agent_lab：第 19～24 章的可复用工程代码，默认合成数据、只读 API。
- tools：课程清单、示例运行、练习验收、原有严格内容校验与补充链接校验。
- tests：保留旧版课程元测试/属性测试，新增 SDK、MCP、持久化、检索和 API 测试。
- solutions：参考答案；chapters：每章说明、例子、待完成练习与验收。
- career：面经、求职路线、系统设计、作品集与资料来源。

## 能力边界

本仓库不是生产 Agent 平台。没有真实 OAuth、多 worker 调度、向量数据库、reranker、完整 tracing，也没有经过真实模型的端到端质量/费用评估。第 17～18 章的手写循环用于理解原理；第 21 章采用真实 LangGraph，但模型工具调用片段并未自动接入这个图。

第 22 章的 5 条合成数据只用于回归演示。API 的公开演示 token 仅供 loopback 本地学习，不得作为生产认证。作品集扩展与未完成能力均有明确标注。
