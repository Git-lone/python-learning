# 第 1 章：基础语法

**先修章节：** 无

本章不追求背完语法，而是先把 Java 的“变量槽位”心智模型切换为 Python 的“名称绑定对象”。

## 学习目标

- 理解名称绑定、动态类型和 `None`，避免把名称等同于带固定类型的变量。
- 使用 `if`、`for`、`range` 和缩进表达分支与循环。
- 使用 f-string 生成可读、可验证的输出。

## Java 对照

### 对照卡：变量与控制流 {#compare-bindings-control-flow}

- 共同用途：保存业务数据，并根据条件选择执行路径。
- 可验证行为差异：Java 变量声明后类型固定；Python 名称可重新绑定到不同对象，代码块由缩进而非花括号界定。
- Python 适用场景：脚本、数据转换和表达紧凑的业务规则。
- Java 开发者常见误区：把类型注解理解成 Java 编译期强制类型，或混用 Tab 与空格。
- 修正方式：先判断对象具有什么行为，统一四空格缩进，并在公共边界使用类型提示。

```java
int score = 82;
String grade = score >= 80 ? "B" : "C";
System.out.printf("grade=%s%n", grade);
```

```python
score = 82
grade = "B" if score >= 80 else "C"
print(f"grade={grade}")
```

## Python 知识

赋值语句把左侧名称绑定到右侧对象；`==` 比较值，`is` 比较对象身份，因此空值判断写成 `value is None`。`for item in items` 直接遍历元素，不需要先写下标循环。

Python 没有 Java 的 `switch` 必需场景：少量分支用 `if/elif/else`，结构化模式再考虑 `match`。布尔上下文中，`None`、数值零以及空字符串和空集合都为假，但业务代码应避免把“缺失”和“合法的零”混为一谈。

## 可运行示例

### 示例：ch01-basics

[ch01_basics.py](examples/ch01_basics.py) 展示名称绑定、聚合、分支和 f-string。从仓库根目录运行：`python -m tools.run_example --chapter 01`。

预期输出包含 `customer=Alice total=60.00` 和 `grade=B items=2`。

## 练习

- `CH01-EX01`：[完成订单描述函数](exercises/exercise_ch01.py)，计算总价并用条件表达式标记订单规模。

先实现正常输入，再手动验证 `quantity=1` 与 `quantity=3` 两条分支。不要使用全局变量保存计算结果。

完成后运行 `python -m tools.check_exercise --chapter 01`；通过后再查看[参考答案](../../solutions/ch01_basics.py)。

## 验证方式

运行 `python -m tools.run_example --chapter 01` 验证示例；运行 `python -m tools.check_exercise --chapter 01` 自动检查正常与批量订单边界。

## 章节总结

Python 的核心不是“省略类型”，而是名称在运行时绑定对象。掌握缩进、直接迭代和 f-string 后，你已经能可靠编写小型命令行逻辑。
