# 第 7 章：文件与上下文管理器

**先修章节：** [第 5 章：异常处理](../05-exceptions/README.md)、[第 6 章：模块与包](../06-modules-packages/README.md)

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 使用 `pathlib.Path` 组合和检查路径，减少平台相关字符串操作。
- 区分文本与二进制 I/O，并为文本显式指定 UTF-8 编码。
- 使用 `with` 管理文件和临时目录，理解上下文管理协议的退出保证。

## Java 对照

### 对照卡：资源生命周期 {#compare-files-context-managers}

- 共同用途：在正常和异常路径都可靠释放文件、锁或连接。
- 可验证行为差异：Python 的 `with` 调用通用的 `__enter__`/`__exit__` 协议，不限于可关闭对象。
- Python 适用场景：文件、临时目录、数据库事务、锁和精度上下文。
- Java 开发者常见误区：依赖操作系统默认编码，或返回文件对象后才尝试读取。
- 修正方式：在 `with` 内完成资源操作，显式写 `encoding="utf-8"`，只把结果传出作用域。

```java
try (var reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
    return reader.lines().count();
}
```

```python
with path.open(encoding="utf-8") as stream:
    lines = sum(1 for line in stream if line.strip())
```

## Python 知识

`Path` 支持 `/` 运算符拼接路径，以及 `read_text`、`write_text`、`open`、`suffix` 等高层操作。大文件应流式读取，不要无条件 `read_text()` 把全部内容载入内存。

上下文管理器的退出方法即使发生异常也会运行。自定义资源可以实现协议，也可以用 `contextlib.contextmanager` 把 `yield` 前后分别作为获取和释放阶段。

### 教案：资源在异常时也要关闭（建议 30 分钟）

1. **先预测（5 分钟）：** 打开文件后，如果解析 JSON 抛异常，后续显式 `close()` 可能不运行。写出用 `with` 管理文件的代码路径，并指出退出代码块时发生什么。
2. **读示例（10 分钟）：** 追踪临时目录、文件写入、读取、退出上下文和关闭状态，区分“临时目录清理”与“文件句柄关闭”两层生命周期。
3. **运行观察（5 分钟）：** 运行示例，核对 JSON 内容和关闭状态。解释为什么文件内容必须显式指定 UTF-8，而不能依赖本机默认编码。
4. **练习与自测（10 分钟）：** 逐行读取并统计去掉空白后仍有内容的行。自测：文件不存在时返回 0 是否合理？不合理；这会把读取失败伪装成合法空文件。

## 可运行示例

### 示例：ch07-files

[ch07_files.py](examples/ch07_files.py) 在临时目录写入并读取 JSON，退出文件上下文后检查关闭状态。运行：`python -m tools.run_example --chapter 07`。

## 练习

- `CH07-EX01`：[统计非空行](exercises/exercise_ch07.py)，要求流式读取 UTF-8 文件。

不要使用 `readlines()`；让不存在的路径自然抛出 `FileNotFoundError`，不要返回含糊的零。

完成后运行 `python -m tools.check_exercise --chapter 07`；通过后再查看[参考答案](../../solutions/ch07_files.py)。

## 验证方式

示例输出应包含 `loaded=2 file_closed=True`。练习检查覆盖正文、空文件、资源关闭和文件不存在场景。

## 章节总结

路径、编码和资源释放都是 I/O 契约的一部分。`pathlib` 与 `with` 能让这些契约清楚地出现在代码里。
