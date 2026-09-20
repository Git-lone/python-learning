"""Small deterministic retrieval regression set; not a production benchmark."""

import json

from agent_lab.retrieval import recall_at_k, reciprocal_rank, retrieve

# 每条样例显式给出相关文档真值；合成小数据集只用于回归，不代表线上准确率。
CASES = (
    ("password reset", "alpha", {"kb-reset"}),
    ("invoice export", "alpha", {"kb-invoice"}),
    ("refund approval", "alpha", {"kb-refund"}),
)


def evaluate() -> dict[str, float | int | str]:
    recalls, ranks = [], []
    for question, tenant, relevant in CASES:
        ids = [hit.document.id for hit in retrieve(question, tenant, 3)]
        recalls.append(recall_at_k(ids, relevant, 3))
        ranks.append(reciprocal_rank(ids, relevant))
    # 分别检查无相关资料和无授权语料，避免只测可回答问题而忽略应当拒答的情况。
    negatives = (("volcano", "alpha"), ("password reset", "unknown"))
    abstentions = sum(not retrieve(question, tenant) for question, tenant in negatives)
    return {
        "dataset": "synthetic-v1",
        "answerable_cases": len(CASES),
        "recall@3": sum(recalls) / len(recalls),
        # 上面只检索前 3 条，因此这里统计的是截断到 3 的平均倒数排名。
        "mrr@3": sum(ranks) / len(ranks),
        "negative_cases": len(negatives),
        "correct_abstentions": abstentions,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), sort_keys=True))
