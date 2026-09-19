"""CH16-EX01 参考答案。"""

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class Document:
    document_id: str
    text: str


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def rank_documents(
    query: str, documents: list[Document], limit: int
) -> list[Document]:
    if limit < 1:
        raise ValueError("limit must be positive")
    query_tokens = _tokens(query)
    # 同时保存 document_id，用作相关性相同情况下的确定性排序键。
    scored = [
        (len(query_tokens & _tokens(document.text)), document.document_id, document)
        for document in documents
    ]
    # 零分文档会制造无依据上下文，因此在截断前剔除。
    return [
        document
        for score, _, document in sorted(scored, key=lambda item: (-item[0], item[1]))
        if score > 0
    ][:limit]
