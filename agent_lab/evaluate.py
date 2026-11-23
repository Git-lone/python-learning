"""第 22 章检索回归入口：用三条可回答问题和两条负例检查确定性检索行为。

真值是人工指定的文档 ID，评测只调用 retrieve，不调用模型。指标可用于比较本课程
修改前后的结果，但样本少且是合成数据，不能外推为线上准确率或端到端问答成功率。
"""

import json

from agent_lab.retrieval import recall_at_k, reciprocal_rank, retrieve

# 每条样例显式给出相关文档真值；合成小数据集只用于回归，不代表线上准确率。
CASES = (
    ("password reset", "alpha", {"kb-reset"}),
    ("invoice export", "alpha", {"kb-invoice"}),
    ("refund approval", "alpha", {"kb-refund"}),
)


def evaluate() -> dict[str, float | int | str]:
    """汇总可回答样本的 Recall@3/MRR@3，并单独报告负例中的正确拒答数量。

    两个排名指标只以 CASES 中的可回答问题为分母；correct_abstentions 是负例
    计数，不是已经除以样本数的比例。分开报告，避免把拒答样本混入召回率口径。
    """

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
