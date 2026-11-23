"""第 22 章词法检索基线：在租户范围内用 BM25 排序，再计算检索指标。

先看 Document/Hit 的数据契约，再看 retrieve 的过滤、分词和排序，最后区分
Recall@K 与倒数排名。所有语料都是本地合成数据；这里没有 embedding、向量数据库
或重排模型，也没有把 BM25 分数转换为可用于业务决策的正确率。
"""

from dataclasses import dataclass
import re

from rank_bm25 import BM25Okapi


@dataclass(frozen=True)
class Document:
    """不可变资料记录：id 用于引用与评测，tenant 决定授权范围，text 用于检索。"""

    id: str
    tenant: str
    text: str


@dataclass(frozen=True)
class Hit:
    """一条检索结果及其排序分数；保留原始文档，避免后续拼接资料时丢失来源。"""

    document: Document
    score: float


# beta 的相似私有资料用于观察租户过滤是否生效；它不是可提供给 alpha 的候选证据。
DOCUMENTS = (
    Document("kb-reset", "alpha", "Password reset: open the recovery page."),
    Document("kb-invoice", "alpha", "Invoice export: use the billing menu."),
    Document("kb-refund", "alpha", "Refund requests require approval by a human."),
    Document("kb-contact", "alpha", "Contact support during business hours."),
    Document("kb-delivery", "alpha", "Delivery tracking is available in the order details."),
    Document("kb-private", "beta", "Password reset: PRIVATE beta recovery code."),
)


def tokens(text: str) -> list[str]:
    """为查询与语料使用同一套简单分词规则，保证词法匹配口径一致。"""

    # 英文按词、中文按单字切分，只是有限的词法基线，不等于成熟中文分词。
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text.lower())


def retrieve(
    question: str, tenant: str, k: int = 3, documents: tuple[Document, ...] = DOCUMENTS
) -> list[Hit]:
    """返回当前租户得分为正的前 k 条资料，空结果交由上层执行拒答。

    每次请求都会用授权语料重新建立 BM25，便于把权限边界与排序过程放在一起学习；
    这不是面向大规模语料的索引管理方案。词面未重合的同义问题也可能没有结果。
    """

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
    """衡量相关资料是否被找全：分母是该问题的全部相关文档，不是返回条数。

    先截取前 k 个结果，再对命中文档去重，防止重复结果虚增召回数；本函数评估
    检索，不判断模型最终回答是否正确、是否真的引用了这些资料。
    """

    if not relevant or k < 1:
        raise ValueError("relevant must be nonempty and k positive")
    # Recall@K = 前 K 个位置命中的不同相关文档数 / 全部相关文档数。
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    """衡量首条相关资料排得多靠前；本函数算单个问题，多个问题平均才得到 MRR。"""

    if not relevant:
        raise ValueError("relevant must be nonempty")
    # 只看首个相关结果的排名，从 1 开始；未命中返回 0，多条查询平均后才是 MRR。
    return next((1.0 / rank for rank, doc in enumerate(retrieved, 1) if doc in relevant), 0.0)
