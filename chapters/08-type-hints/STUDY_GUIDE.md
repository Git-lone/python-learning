# 第 8 章学案：类型提示与 Protocol

配合[本章讲解](README.md)使用，区分静态类型检查与运行时校验。

## 类型提示和 Protocol 是什么

类型提示描述函数接受与返回什么形状的数据，供阅读者、编辑器和静态检查器使用；Python 运行时默认不会按注解拦截错误输入。`Protocol` 定义“具有哪些成员就可使用”的结构化接口：对象不必显式继承它，也能满足调用方的静态合同。

## 组成与使用场景

本章用内置泛型 `list[str]`、联合类型 `str | None`、`TypeVar` 和 `typing.Protocol`，配合 mypy 静态检查。适合公共 API、模型适配端口和可替换的存储实现。Java 开发者可以把 `Protocol` 想作调用方视角的接口，但要记住它不是运行时数据校验器。

外部 JSON 即使标注为 `dict[str, int]`，实际字段仍可能缺失或含字符串；入口层仍要解析和验证。把类型写成 `Any` 虽能压住静态警告，却会把错误推迟到运行时。

## 代码怎样工作

[示例](examples/ch08_types.py)定义 `Priced` 所需成员，`Product` 只要提供相同结构即可交给调用方。[练习](exercises/exercise_ch08.py)用类型变量保留输入元素与返回元素的关系，对任意可迭代对象只取第一项；生成器不需要先转列表。

## 课前热身

- Java 接口通常要求显式实现；如果 Python 对象有同名属性或方法，怎样表达调用方所需的行为？
- HTTP JSON 标上 `dict[str, int]`，是否自动验证真实数据？

## 探究任务

1. 阅读[示例](examples/ch08_types.py)，找到 `Priced` 需要的成员，以及 `Product` 如何满足它。预测是否需要显式继承：________。
2. 运行 `python -m tools.run_example --chapter 08`，再运行 `python -m mypy`。记录静态检查与运行输出分别证明什么：________。
3. 设输入是一个生成器，若先 `list(source)` 再取首项，会提前做多少工作？________。

## 动手完成

- 在[练习](exercises/exercise_ch08.py)用类型变量保留元素类型，并只消费首项。
- 运行 `python -m tools.check_exercise --chapter 08`。记录空输入和非空输入的结果：________。

## 过关自检

- 能解释 `Protocol` 的结构化匹配。
- 能指出类型提示不会替代外部输入校验。
- 能写出 `str | None` 与 `list[str]`。完成后再看[参考答案](../../solutions/ch08_types.py)。
