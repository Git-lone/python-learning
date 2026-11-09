# 第 6 章：模块与包

**先修章节：** [第 1 章：基础语法](../01-basics/README.md)、[第 3 章：函数与装饰器](../03-functions-decorators/README.md)

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 区分模块、普通包、导入路径和文件系统路径。
- 使用 `__init__.py` 与 `__all__` 暴露小而稳定的公共 API。
- 理解 `__name__ == "__main__"`，避免导入模块时意外执行脚本逻辑。

## Java 对照

### 对照卡：包与导入 {#compare-modules-packages}

- 共同用途：组织代码、控制可见名称并管理模块间依赖。
- 可验证行为差异：Python 首次导入会执行模块顶层语句，模块本身也是运行时对象。
- Python 适用场景：按领域拆包，并通过包入口提供稳定函数和类型。
- Java 开发者常见误区：认为目录天然等同于 Java package，或从任意工作目录直接运行深层文件。
- 修正方式：从仓库根目录运行，优先 `python -m package.module`，保持导入时无副作用。

```java
import com.example.order.Pricing;
var total = Pricing.grossTotal(amounts);
```

```python
from order_tools import gross_total

total = gross_total(amounts)
```

## Python 知识

一个 `.py` 文件就是模块，含 `__init__.py` 的目录是普通包。绝对导入更易跨包理解，包内部紧密相关模块可用显式相对导入，例如 `from .pricing import gross_total`。

模块顶层应主要放常量、定义和轻量注册。命令行入口放进 `main()`，再由名称保护语句调用，这样测试和其他模块可以安全导入。

### 教案：建立清楚的包边界（建议 30 分钟）

1. **场景导入（5 分钟）：** 假设订单价格逻辑要被 CLI、测试和其他模块同时调用。先决定哪些名称属于包的公共入口，哪些只在包内部使用。
2. **沿导入链追踪（10 分钟）：** 从示例的 `import` 开始，找到 `order_tools/__init__.py` 暴露的函数，再追到实现模块。对照 Java package，说明 Python 导入会执行模块顶层代码。
3. **运行观察（5 分钟）：** 运行示例并核对价格输出。思考如果顶层直接读取键盘或启动服务，测试只想导入价格函数时会发生什么。
4. **练习与自测（10 分钟）：** 将订单号规范化分成“清理前缀、校验输入、格式化序号”三步。自测：`if __name__ == "__main__"` 保护的是哪类动作？只应在直接运行文件时执行的入口动作。

## 可运行示例

### 示例：ch06-modules

[ch06_modules.py](examples/ch06_modules.py) 从 [order_tools](examples/order_tools/__init__.py) 的公共入口导入价格函数。运行：`python -m tools.run_example --chapter 06`。

## 练习

- `CH06-EX01`：[实现 build_order_id](exercises/exercise_ch06.py)，输出规范化的固定宽度订单编号。

去掉前缀两端空格、转成大写，并拒绝空前缀和负序号。

完成后运行 `python -m tools.check_exercise --chapter 06`；通过后再查看[参考答案](../../solutions/ch06_modules.py)。

## 验证方式

示例输出应包含 `public_api=30.00` 和 `module_name=__main__`。练习检查覆盖前缀规范化、补零以及非法输入。

## 章节总结

模块边界就是依赖边界。导入时无副作用、入口明确、公共 API 小而稳定，能显著降低 Python 项目的维护成本。
