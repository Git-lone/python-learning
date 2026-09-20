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
    # 英文按词、中文按单字切分，只是有限的词法基线，不等于成熟中文分词。
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text.lower())


def retrieve(
    question: str, tenant: str, k: int = 3, documents: tuple[Document, ...] = DOCUMENTS
) -> list[Hit]:
    if not 1 <= k <= 5:
        raise ValueError("k must be between 1 and 5")
    # 先按租户授权范围过滤，再检索；不能先搜全库，再指望模型自行忽略私有资料。
    corpus = [doc for doc in documents if doc.tenant == tenant and tokens(doc.text)]
    query = tokens(question)
    if not corpus or not query:
        return []
    # BM25 使用词频和逆文档频率，不是向量语义检索；小语料分数会受词分布明显影响。
    model = BM25Okapi([tokens(doc.text) for doc in corpus])
    scores = model.get_scores(query)
    # 当前基线仅保留正分结果，无结果就拒答；分数不是概率，也不是已校准的置信度。
    hits = [Hit(doc, float(score)) for doc, score in zip(corpus, scores, strict=True) if score > 0]
    # 同分按文档 ID 排序，使回归测试与引用顺序可重复。
    return sorted(hits, key=lambda hit: (-hit.score, hit.document.id))[:k]


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant or k < 1:
        raise ValueError("relevant must be nonempty and k positive")
    # Recall@K = 前 K 个位置命中的不同相关文档数 / 全部相关文档数。
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    if not relevant:
        raise ValueError("relevant must be nonempty")
    # 只看首个相关结果的排名，从 1 开始；未命中返回 0，多条查询平均后才是 MRR。
    return next((1.0 / rank for rank, doc in enumerate(retrieved, 1) if doc in relevant), 0.0)
