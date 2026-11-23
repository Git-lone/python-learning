"""第 22 章参考解答：计算检索结果前 k 个位置的召回率。

请先独立完成练习再阅读。该指标检验相关文档是否被找到，不评价答案是否
正确、引用是否忠实，也不衡量检索延迟；它只是 RAG 评测中的一个维度。
"""


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """按文档标识计算命中相关文档的比例，返回 0 到 1 之间的数。

    retrieved 按检索排名排列，relevant 是该问题的完整相关文档标注集合。
    未提供相关文档或 k 不为正数时拒绝计算，避免给无定义的指标填入零。
    标注遗漏会改变分母，因此比较不同检索方案时应使用同一套标注。
    """
    if not relevant or k < 1:
        raise ValueError("relevant must be nonempty and k positive")
    # 先截取前 k 个位置，再去重；分母是全部相关文档数，不是返回结果数。
    # 重复文档占用排名位置，却不能重复计分；结果不足 k 条时使用实际返回内容。
    return len(set(retrieved[:k]) & relevant) / len(relevant)
