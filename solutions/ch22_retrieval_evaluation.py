"""Reference answer for CH22; inspect only after attempting the exercise."""


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant or k < 1:
        raise ValueError("relevant must be nonempty and k positive")
    return len(set(retrieved[:k]) & relevant) / len(relevant)
