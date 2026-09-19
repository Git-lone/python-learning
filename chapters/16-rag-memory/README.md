# 第 16 章：检索增强与对话记忆

**先修章节：** [第 2 章：集合与推导式](../02-collections-comprehensions/README.md)、[第 7 章：文件与上下文管理器](../07-files-context-managers/README.md)、[第 8 章：类型提示](../08-type-hints/README.md)、[第 9 章：迭代器与生成器](../09-iterators-generators/README.md)、[第 14 章：LLM 应用基础](../14-llm-application-basics/README.md)

模型参数不是企业知识库。RAG 在调用模型前选择相关证据，记忆则选择本轮需要保留的交互状态。

## 学习目标

- 理解文档加载、切分、索引、检索、排序和引用组成的 RAG 管线。
- 实现可解释的词项重叠检索基线，再理解 Embedding 检索替换的是哪一层。
- 使用有界短期记忆，避免把完整历史无限追加到模型上下文。

## Java 对照

### 对照卡：检索上下文与缓存 {#compare-retrieval-memory}

- 共同用途：从大量数据中选择当前请求需要的少量信息。
- 可验证行为差异：RAG 结果会直接进入模型上下文，除了相关性还必须保留来源、权限和版本信息。
- Python 适用场景：内部知识问答、客服、代码库助手和长期任务 Agent。
- Java 开发者常见误区：把向量数据库当成普通缓存，认为距离最近就必然真实、可见且最新。
- 修正方式：先做可解释基线，再加入语义检索、重排、权限过滤、引用和离线评测。

```java
List<Document> context = retriever.search(query, limit);
```

```python
# 检索器只负责选证据；回答层仍需携带来源并允许“没有答案”。
context = retrieve(query, documents, limit=3)
```

## Python 知识

最小 RAG 管线是：读取文档 → 切分块 → 建立索引 → 查询召回 → 重排 → 构造带引用上下文 → 生成回答。Embedding 可以改善语义召回，但不能替代访问控制、更新策略和答案评测。

对话记忆至少分为短期窗口、摘要和外部长期事实。记忆写入也是副作用：应明确保存什么、保存多久、如何删除，以及哪些内容绝不能持久化。

## 可运行示例

### 示例：ch16-rag-memory

[ch16_rag_memory.py](examples/ch16_rag_memory.py) 用词项重叠选择文件处理文档，并用 `deque(maxlen=2)` 保持有界对话窗口。运行：`python -m tools.run_example --chapter 16`。

## 练习

- `CH16-EX01`：[实现 rank_documents](exercises/exercise_ch16.py)，按共享词数降序，并用文档 ID 提供稳定的平分规则。

零分文档不应返回，`limit` 必须为正数。完成后运行 `python -m tools.check_exercise --chapter 16`，再查看带注释的[参考答案](../../solutions/ch16_rag_memory.py)。

## 验证方式

示例应选择 `files` 文档且记忆长度保持为 2。练习检查覆盖相关性排序、稳定平分、无结果、数量限制和非法限制。

## 章节总结

RAG 不是“接上向量库”这么简单。可靠系统需要可追踪来源、权限过滤、无答案路径和评测集；记忆也必须有明确预算与删除策略。
