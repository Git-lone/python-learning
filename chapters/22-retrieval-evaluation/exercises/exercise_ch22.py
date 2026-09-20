"""正确计算 Recall@K，不能重复计数。实现后运行本章验收；不要先复制参考答案。"""


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    # retrieved 按排名排列，relevant 是相关文档真值；同一文档重复出现不能重复得分。
    # 只评估前 k 个位置，空真值集合或非正 k 抛 ValueError。
    raise NotImplementedError("Implement CH22-EX01")
