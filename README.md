# 面向 Java 开发者的 Python 学习路线

本课程面向已经具备 **Java 基础语法、集合、面向对象和异常处理经验** 的开发者，通过 Java/Python 对照、可运行示例和练习逐章迁移到 Python。课程的机器可读章节清单位于 [`learning/catalog.toml`](learning/catalog.toml)，紧凑章节索引位于 [`learning/INDEX.md`](learning/INDEX.md)。

## 运行环境与工具

所有命令均从仓库根目录非交互执行；教学运行时代码仅使用 Python 标准库。

| 工具 | 兼容版本 | 当前锁定版本 |
|---|---|---|
| Python | `>=3.12,<3.14` | 由本机安装提供 |
| pytest | `>=8.3,<10` | `8.3.5` |
| Hypothesis | `>=6.100,<7` | `6.127.5` |
| mypy | `>=1.14,<2` | `1.15.0` |

Windows 下建议显式选择受支持的 Python 3.13（如果默认 `python` 已指向 3.14，这一步尤其重要），然后安装锁定依赖：

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.lock
```

macOS/Linux 可把第一条命令替换为 `python3.13 -m venv .venv`。

激活虚拟环境后可使用以下平台中立的通用命令：

```powershell
python -m tools.run_example --all
python -m mypy learning tools
python -m pytest -q
python -m tools.validate_content
```

依次对应全部示例运行、静态检查、测试运行和内容一致性检查；命令均不读取键盘输入，也不要求图形界面。

## 练习工作流

每章练习文件保留 `NotImplementedError`，建议按“先实现、再验收、最后看答案”的顺序学习：

```powershell
python -m tools.check_exercise --chapter 01
python -m tools.check_exercise --chapter 01 --solution
python -m tools.check_exercise --all --solution
```

第一条检查你填写的练习，第二条用同一组测试运行参考答案，第三条验证全部参考答案。章节编号也可写成 `1` 或 `CH01`。

## 完整学习顺序

| 编号 | 主题 | 先修章节 | 唯一入口 |
|---:|---|---|---|
| 1 | 基础语法 | 无 | [进入第 1 章](learning/chapters/01-basics/README.md) |
| 2 | 集合与推导式 | [第 1 章](learning/chapters/01-basics/README.md) | [进入第 2 章](learning/chapters/02-collections-comprehensions/README.md) |
| 3 | 函数与装饰器 | [第 1 章](learning/chapters/01-basics/README.md)、[第 2 章](learning/chapters/02-collections-comprehensions/README.md) | [进入第 3 章](learning/chapters/03-functions-decorators/README.md) |
| 4 | 面向对象与数据类 | [第 1 章](learning/chapters/01-basics/README.md)、[第 3 章](learning/chapters/03-functions-decorators/README.md) | [进入第 4 章](learning/chapters/04-oop-dataclasses/README.md) |
| 5 | 异常处理 | [第 1 章](learning/chapters/01-basics/README.md)、[第 3 章](learning/chapters/03-functions-decorators/README.md) | [进入第 5 章](learning/chapters/05-exceptions/README.md) |
| 6 | 模块与包 | [第 1 章](learning/chapters/01-basics/README.md)、[第 3 章](learning/chapters/03-functions-decorators/README.md) | [进入第 6 章](learning/chapters/06-modules-packages/README.md) |
| 7 | 文件与上下文管理器 | [第 5 章](learning/chapters/05-exceptions/README.md)、[第 6 章](learning/chapters/06-modules-packages/README.md) | [进入第 7 章](learning/chapters/07-files-context-managers/README.md) |
| 8 | 类型提示 | [第 3 章](learning/chapters/03-functions-decorators/README.md)、[第 4 章](learning/chapters/04-oop-dataclasses/README.md)、[第 6 章](learning/chapters/06-modules-packages/README.md) | [进入第 8 章](learning/chapters/08-type-hints/README.md) |
| 9 | 迭代器与生成器 | [第 2 章](learning/chapters/02-collections-comprehensions/README.md)、[第 3 章](learning/chapters/03-functions-decorators/README.md) | [进入第 9 章](learning/chapters/09-iterators-generators/README.md) |
| 10 | 同步并发与异步并发 | [第 3 章](learning/chapters/03-functions-decorators/README.md)、[第 5 章](learning/chapters/05-exceptions/README.md)、[第 9 章](learning/chapters/09-iterators-generators/README.md) | [进入第 10 章](learning/chapters/10-concurrency-asyncio/README.md) |
| 11 | 自动化测试 | [第 3 章](learning/chapters/03-functions-decorators/README.md)、[第 5 章](learning/chapters/05-exceptions/README.md)、[第 6 章](learning/chapters/06-modules-packages/README.md)、[第 8 章](learning/chapters/08-type-hints/README.md) | [进入第 11 章](learning/chapters/11-automated-testing/README.md) |

请按编号顺序学习；每个先修链接只指向当前章节之前的入口。

## 综合项目

完成 11 章后进入[任务进度报告器](learning/capstone/README.md)。它把数据类、模块、文件、异常、生成器、类型提示、命令行接口和 pytest 测试组合成一个可运行的小项目，并提供四个渐进挑战。
