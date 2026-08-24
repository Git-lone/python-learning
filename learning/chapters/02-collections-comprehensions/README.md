# 第 2 章：集合与推导式

**先修章节：** [第 1 章：基础语法](../01-basics/README.md)

## 学习目标

- 根据顺序、可变性、唯一性和查找方式选择 `list`、`tuple`、`set` 或 `dict`。
- 掌握半开区间切片、解包和安全的字典访问。
- 使用推导式完成简单筛选与映射，并知道何时改回普通循环。

## Java 对照

### 对照卡：集合转换 {#compare-collections-comprehensions}

- 共同用途：保存、筛选、转换、去重和聚合一组业务数据。
- 可验证行为差异：Python 推导式直接构造新集合；切片采用包含起点、不包含终点的半开区间。
- Python 适用场景：中小规模内存数据的清洗、索引和聚合。
- Java 开发者常见误区：为每次转换机械照搬 Stream 链，或在遍历时修改原列表。
- 修正方式：单层映射和筛选优先推导式，出现多分支或副作用时使用普通循环。

```java
List<Integer> squares = numbers.stream()
    .filter(n -> n % 2 == 0)
    .map(n -> n * n)
    .toList();
```

```python
squares = [number**2 for number in numbers if number % 2 == 0]
```

## Python 知识

`list` 有顺序且可变，`tuple` 有顺序且通常表达固定结构，`set` 负责唯一性和集合运算，`dict` 保存键值映射。切片 `items[start:stop:step]` 产生新序列；负下标从尾部计数。

解包让结构更清楚：`country, amount, paid = order`。读取可能不存在的键可用 `mapping.get(key)`，但如果缺失本身是程序错误，应保留 `mapping[key]` 让错误尽早暴露。

## 可运行示例

### 示例：ch02-collections

[ch02_collections.py](examples/ch02_collections.py) 用元组保存订单，用集合推导式去重，并用字典推导式计算平方。运行：`python -m tools.run_example --chapter 02`。

## 练习

- `CH02-EX01`：[实现 even_squares](exercises/exercise_ch02.py)，只保留偶数并返回“数字 → 平方”映射。

输入可能包含重复值；利用字典键唯一性得到稳定结果，不要先把可迭代对象强制转换为列表。

完成后运行 `python -m tools.check_exercise --chapter 02`；通过后再查看[参考答案](../../solutions/ch02_collections.py)。

## 验证方式

示例输出应包含 `paid_total=198 countries=DE,FR`。练习检查覆盖重复值、一次性迭代器和空输入。

## 章节总结

集合类型表达了数据约束。先选对结构，再使用推导式表达简单转换，代码通常会比逐字翻译 Java 集合逻辑更直接。
