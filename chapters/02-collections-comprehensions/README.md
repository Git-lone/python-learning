# 第 2 章：集合与推导式

**先修章节：** [第 1 章：基础语法](../01-basics/README.md)

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

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

### 一条订单为什么用元组，一批订单为什么用列表？

**元组（`tuple`）是按位置保存一组值的序列。** 元素可以是不同类型；元组建好后，不能增删元素，也不能替换某个位置上的值。来看本章第一条订单：

```python
order = ("DE", 120, True)       # 一条订单：国家、金额、是否已支付
country, amount, paid = order   # 从左到右取出三个值，这叫“解包”
print(country, amount, paid)    # DE 120 True
```

用 Java 表达同一条业务数据，可以定义 `record Order(String country, int amount, boolean paid) {}`，再用 `new Order("DE", 120, true)` 创建订单。区别在于：Java 用 `order.amount()` 按名字读金额；普通元组没有字段名，`order[1]` 是金额，只因为我们约定把金额放在第二个位置。即使把解包写成 `amount, country, paid = order`，Python 也不会按名字匹配：此时 `amount` 是 `"DE"`。如果订单要跨模块传递，第 4 章的数据类能让字段含义更清楚。

示例外面还有一层列表 `orders = [order]`，类似 Java 的 `ArrayList<Order>` 里装了一条订单。用 `orders.append(("FR", 78, True))` 可以加入下一条：**列表增长了，原来的元组没变。**

现在读示例里的 `sum(amount for _, amount, paid in orders if paid)`。先把它展开成循环：

```python
paid_total = 0
for _, amount, paid in orders:  # 每次取一条订单；_ 接收本次不用的国家
    if paid:
        paid_total += amount
```

对配套示例里的三条订单，总额依次是 `120`、`198`、`198`。最后一条金额 `42` 没有计入，因为它未支付。这里的 `_` 是普通变量名，表示“取到这个值，但后面不用”。

### 其他容器怎么选？

如果只问“出现过哪些国家”，用 `set`（类似 Java 的 `HashSet`，重复的国家只保留一份）；如果还要问“某个国家对应什么金额”，用 `dict`（字典，类似 `Map`，按键取值）。读取不存在的键时，`amounts.get("IT")` 默认返回 `None`，而 `amounts["IT"]` 会抛出 `KeyError`。前者适合“没有也正常”，后者适合“这里必须有值”。

如果要取连续几条明细，用**切片**：`items[start:stop]` 取左端点、不取右端点。列表切片与 Java 的 `subList(start, stop)` 在边界上相似，但前者返回新的列表，后者是原列表的视图。试着预测两行输出：

```python
countries = ["DE", "FR", "IT"]
first_two = countries[:2]       # 省略起点就是从开头取
first_two[0] = "ES"
print(first_two)               # ['ES', 'FR']
print(countries)               # ['DE', 'FR', 'IT']
```

这里替换的是新列表里的一个位置。切片不会递归复制元素；如果元素本身是可变对象，两个列表仍可能指向同一个对象。再拿原列表试两种读法：`countries[-1]` 从末尾取一个值，得到 `"IT"`；`countries[::2]` 从头开始每隔一个位置取一次，得到 `["DE", "IT"]`。第二个冒号后面的数是步长。

### 教案：为数据选择集合（建议 30 分钟）

1. **场景导入（5 分钟）：** 一批订单既要保留输入顺序，又要去重国家，还要按编号快速查找。先分别选 `list`、`set` 和 `dict`，说明每种结构保留或丢失了什么信息。
2. **沿示例讲解（10 分钟）：** 看元组如何表示一条订单、集合推导式怎样去重、字典推导式怎样生成键值。把推导式口头展开为普通 `for` 循环，逐次说出键和值。
3. **动手观察（5 分钟）：** 在练习里输入 `[2, 2, 3, 4]`，先预测结果只含 2 和 4，再解释重复的 2 为什么不会生成两个字典条目。
4. **自测（10 分钟）：** 如果输入是只可遍历一次的生成器，先转列表会有什么代价？会提前消费全部元素并占用额外内存；能直接遍历就直接遍历。完成练习后再检查空输入。

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
