"""BM25 lexical baseline, not a vector database or a semantic search claim."""

from dataclasses import dataclass
import re

from rank_bm25 import BM25Okapi


@dataclass(frozen=True)
class Document:
    id: str
    tenant: str
    text: str


@dataclass(frozen=True)
class Hit:
    document: Document
    score: float


DOCUMENTS = (
    Document("kb-reset", "alpha", "Password reset: open the recovery page."),
    Document("kb-invoice", "alpha", "Invoice export: use the billing menu."),
    Document("kb-refund", "alpha", "Refund requests require approval by a human."),
    Document("kb-contact", "alpha", "Contact support during business hours."),
    Document("kb-delivery", "alpha", "Delivery tracking is available in the order details."),
    Document("kb-private", "beta", "Password reset: PRIVATE beta recovery code."),
)


def tokens(text: str) -> list[str]:
    # English words plus individual CJK characters: intentionally a limited baseline.
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text.lower())


def retrieve(
    question: str, tenant: str, k: int = 3, documents: tuple[Document, ...] = DOCUMENTS
) -> list[Hit]:
    if not 1 <= k <= 5:
        raise ValueError("k must be between 1 and 5")
    corpus = [doc for doc in documents if doc.tenant == tenant and tokens(doc.text)]
    query = tokens(question)
    if not corpus or not query:
        return []
    model = BM25Okapi([tokens(doc.text) for doc in corpus])
    scores = model.get_scores(query)
    # Zero/no positive evidence is abstention, not a confidence probability.
    hits = [Hit(doc, float(score)) for doc, score in zip(corpus, scores, strict=True) if score > 0]
    return sorted(hits, key=lambda hit: (-hit.score, hit.document.id))[:k]


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant or k < 1:
        raise ValueError("relevant must be nonempty and k positive")
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    if not relevant:
        raise ValueError("relevant must be nonempty")
    return next((1.0 / rank for rank, doc in enumerate(retrieved, 1) if doc in relevant), 0.0)
