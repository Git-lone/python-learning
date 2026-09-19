"""练习：实现确定性、可解释的词项检索。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Document:
    document_id: str
    text: str


def rank_documents(
    query: str, documents: list[Document], limit: int
) -> list[Document]:
    """按查询词重叠数降序，分数相同时按 document_id 排序。"""
    # TODO：统一小写并提取字母数字词项，零分文档不得进入结果。
    # 稳定平分规则使同一输入在不同机器上得到相同顺序。
    raise NotImplementedError("请完成 CH16-EX01")
