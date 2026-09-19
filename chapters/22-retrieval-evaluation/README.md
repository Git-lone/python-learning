# 第 22 章：检索实现与离线评测

先修：第 11、16、19 章。本章用成熟的 `rank-bm25` 实现词法检索，替换“关键词重合就是完整 RAG”的误解。

## 学习目标

- 对检索相关性与无证据拒答进行可重复评估。
- 公开数据集规模、切分方式和指标口径。
- 完成“正确计算 Recall@K，不能重复计数”并解释失败测试的意义。

## Java 对照

### 检索实现与离线评测 {#compare-retrieval-evaluation}

- 共同用途：对检索相关性与无证据拒答进行可重复评估。
- 可验证行为差异：集合去重和切片边界决定指标含义，不能将 Python list 长度当召回率。
- Python 适用场景：版本回归、分桶分析和检索消融。
- Java 开发者常见误区：拿三条合成题的满分宣称线上准确率。
- 修正方式：公开数据集规模、切分方式和指标口径。



搜索逻辑与语言无关：先确定可访问文档，再切词、召回、排序。Python 集合交集能简洁计算命中，但指标分母必须事先定义。不能用模型说自己答对了替代测试。

## Python 知识

### 实现与限制

[retrieval.py](../../agent_lab/retrieval.py) 先过滤 tenant，再构建 BM25 词法索引；分数为 0 或没有正分证据时拒绝召回。英文词和中文单字切分只是低成本基线，既非语义向量，也不是中文专业分词方案。

BM25 分数不是概率，小语料 IDF 会不稳定；单文档或多数文档共享关键词时，本例的正分规则可能过度拒答。它只适合演示已给定的样本，不要把阈值直接复制到生产。

[evaluate.py](../../agent_lab/evaluate.py) 固定 3 条可回答题、2 条负例，检查答案文档召回和拒答行为：

## 可运行示例

### 运行记录：ch22-demo

```powershell
python -m tools.run_example --chapter 22
python -m agent_lab.evaluate
python -m pytest tests/test_retrieval.py -q
```

这 5 个合成样本的满分只证明回归样例通过，**不代表真实用户准确率**。这里评的是检索与拒答，没有调用模型，所以也没有测生成质量。

### 指标口径

| 指标 | 本章定义 | 不能说明什么 |
|---|---|---|
| Recall@K | 前 K 条中的不同相关文档数 / 全部相关文档数 | 生成答案是否正确 |
| MRR@K | 每题前 K 条中第一个相关文档排名的倒数，再平均 | 全部相关证据是否齐全 |
| 负例正确拒答数 | 无答案/无权限题中未召回证据的数量 | 系统对所有危险输入都安全 |

没有相关文档的题单独评拒答，不给 Recall 分母塞入 0。重复召回同一文档不能重复记功。

## 练习

完成 [exercise_ch22.py](exercises/exercise_ch22.py) 的 Recall@K，空 relevant 或 k<1 抛 `ValueError`；空召回为 0。

```powershell
python -m tools.check_exercise --chapter 22
python -m tools.check_exercise --chapter 22 --solution
```

[参考答案](../../solutions/ch22_retrieval_evaluation.py)。随后收集至少 30 条脱敏或自制问题，分训练调参集与独立测试集，保留问题、相关文档、无答案原因和版本号。

拓展尚未实现：接入 embedding + 向量库，加入混合召回、去重与 reranker，比较 BM25、向量、混合、重排四组。每组记录 Recall、MRR、延迟和成本；去掉其中一项再测，这才是可解释的消融实验。

面试追问“RAG 不准怎么办”：先定位文档解析/更新、切分、召回、重排、上下文拼装还是生成出错，查看同一 request 的证据链；不要首先换更贵的模型。

检索库依据：[rank_bm25 项目](https://github.com/dorianbrown/rank_bm25)。权限不应由模型传入的 tenant 决定，服务入口见下一章。

## 验证方式

运行 `python -m tools.check_exercise --chapter 22` 验证自己的实现，`--solution` 用于核对参考答案。示例合同由 `python -m tools.run_example --chapter 22` 验证；工程异常测试见根目录 tests。

## 章节总结

公开数据集规模、切分方式和指标口径。面试时同时说明实现、测试证据和未实现边界；公开原帖与自编练习分别见 [真实面经](../../career/INTERVIEW_EXPERIENCES.md) 和 [面试练习](../../career/INTERVIEW_PRACTICE.md)。
