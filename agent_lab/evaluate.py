"""Small deterministic retrieval regression set; not a production benchmark."""

import json

from agent_lab.retrieval import recall_at_k, reciprocal_rank, retrieve

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
    negatives = (("volcano", "alpha"), ("password reset", "unknown"))
    abstentions = sum(not retrieve(question, tenant) for question, tenant in negatives)
    return {
        "dataset": "synthetic-v1",
        "answerable_cases": len(CASES),
        "recall@3": sum(recalls) / len(recalls),
        "mrr@3": sum(ranks) / len(ranks),
        "negative_cases": len(negatives),
        "correct_abstentions": abstentions,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), sort_keys=True))
