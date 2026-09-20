"""Reference answer for CH22; inspect only after attempting the exercise."""


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant or k < 1:
        raise ValueError("relevant must be nonempty and k positive")
    # 先截取前 k 个位置，再去重；分母是全部相关文档数，不是返回结果数。
    return len(set(retrieved[:k]) & relevant) / len(relevant)
