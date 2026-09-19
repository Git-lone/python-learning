# 综合项目：任务进度报告器

这个阶段性命令行项目把前 11 章知识串成一条完整路径：领域数据类、包结构、JSON 文件、异常链、生成器、类型提示、命令行入口和 pytest 测试。完成后继续第 12～18 章，进入 LLM、AI Agent 与 Harness 循环工程。

## 运行基线

从仓库根目录运行：

```powershell
python -m capstone.starter.task_reporter --input capstone/sample_tasks.json
```

输出包含完成率以及按负责人、标题排序的未完成任务。还可以增加 `--owner Alice` 过滤负责人。

## 代码地图

- [model.py](starter/task_reporter/model.py)：不可变 `Task` 数据类和外部数据校验。
- [repository.py](starter/task_reporter/repository.py)：UTF-8 JSON 读取、异常转换与异常链。
- [report.py](starter/task_reporter/report.py)：集合聚合、惰性筛选和报告渲染。
- [cli.py](starter/task_reporter/cli.py)：参数解析、错误出口和负责人过滤。
- [test_task_reporter.py](test_task_reporter.py)：正常路径、异常路径和 CLI 行为测试。

## 渐进挑战

1. 增加 `status` 枚举和截止日期，并保持旧 JSON 仍可读取。
2. 使用第 10 章知识并发读取多个 `--input` 文件，同时限制并发数。
3. 添加 `--format json` 输出，但让领域层不依赖 `argparse`。
4. 为重复任务、空文件、未知字段和负工时补充参数化测试。

## 完成标准

在项目根目录 `C:\workspace\my\py\learning` 运行 `python -m pytest capstone/test_task_reporter.py -q`、`python -m mypy` 和 `python -m tools.validate_content`，三条命令都应成功。类型检查默认覆盖新增的 `agent_lab` 与 `tools`；旧章节练习由各章验收测试验证。
