# 第 12 章：配置、命令行与日志

**先修章节：** [第 5 章：异常处理](../05-exceptions/README.md)、[第 6 章：模块与包](../06-modules-packages/README.md)、[第 8 章：类型提示](../08-type-hints/README.md)、[第 11 章：自动化测试](../11-automated-testing/README.md)

本章把可以运行的 Python 文件提升为可部署、可诊断的应用，为后续模型客户端和 Agent 运行时建立工程边界。

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 把字符串环境变量一次性解析为不可变、强类型配置对象。
- 使用 `argparse` 设计非交互命令行入口，并用退出码区分成功与失败。
- 使用 `logging` 的级别、Logger、Handler 和 Formatter 记录可诊断事件。

## Java 对照

### 对照卡：应用配置与日志 {#compare-configuration-logging}

- 共同用途：在代码外提供运行参数，并为生产问题留下可查询证据。
- 可验证行为差异：Python 的 `os.environ` 始终返回字符串；`logging` 通过 Logger 与 Handler 组合输出目标。
- Python 适用场景：CLI、批处理、Web 服务、模型客户端和 Agent 运行时。
- Java 开发者常见误区：期待环境变量像 Spring `@ConfigurationProperties` 一样自动完成类型转换与校验。
- 修正方式：在入口层解析一次，转换为冻结数据类；业务函数只依赖已经有效的配置对象。

```java
record Settings(String host, int port, boolean debug) {}
```

```python
@dataclass(frozen=True, slots=True)
class Settings:
    host: str
    port: int
    debug: bool
```

## Python 知识

配置优先级通常是“命令行参数 > 环境变量 > 明确默认值”。解析失败应在启动阶段立即报告，而不是让错误字符串进入深层业务代码。密钥只能从安全配置读取，不能写入源码、日志或异常消息。

库代码不要调用 `logging.basicConfig()`；它属于应用入口。日志记录事件和上下文，不记录完整提示词、访问令牌或用户敏感数据。Agent 轨迹尤其需要区分可审计元数据与不可落盘内容。

### 教案：在入口处消化不可信配置（建议 30 分钟）

1. **场景导入（5 分钟）：** 服务从环境变量读取端口和调试开关。先判断字符串 `"false"` 的布尔值为何不能直接用 `bool(...)`，再列出两个非法端口。
2. **读示例（10 分钟）：** 跟踪环境映射注入、值解析、日志级别选择和日志写入。指出哪些配置应在启动时拒绝，哪些可使用明确默认值。
3. **运行观察（5 分钟）：** 运行示例，核对环境与日志级别。讨论日志里保留事件名和错误码即可排障的场景，以及为何不记录令牌和完整提示词。
4. **练习与自测（10 分钟）：** 分别输入端口 `1`、`65535`、`0` 与布尔值 `TRUE`、`maybe`。自测：为什么要把解析后的值放进强类型配置对象？让深层业务代码不再重复猜测字符串含义。

## 可运行示例

### 示例：ch12-configuration

[ch12_configuration.py](examples/ch12_configuration.py) 注入固定环境映射，解析日志级别，并把日志写入可验证的内存流。运行：`python -m tools.run_example --chapter 12`。

## 练习

- `CH12-EX01`：[实现 load_settings](exercises/exercise_ch12.py)，解析主机、端口和调试开关。

端口必须位于 `1..65535`；布尔值只接受大小写不敏感的 `true` 或 `false`。完成后运行 `python -m tools.check_exercise --chapter 12`，再查看[参考答案](../../solutions/ch12_configuration.py)。

## 验证方式

示例应输出 `environment=dev level=INFO`。练习检查覆盖默认值、正常转换、非法端口和未知布尔值；参考答案可用 `python -m tools.check_exercise --chapter 12 --solution` 验证。

## 章节总结

把字符串配置限制在入口层，能让内部代码保持强类型。清晰的 CLI 退出码和安全日志是后续网络调用与 Agent 自动化能够被运维的前提。
