"""CH16-EX01 参考答案：实现可解释、可离线验证的关键词检索基线。

只比较查询和文档的英文数字词集合，不生成 embedding、不访问向量库，
也没有调用模型生成答案；它对应 RAG 中提供候选材料的检索环节。
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class Document:
    """用文档标识和正文携带检索材料，标识也用于同分时的排序。

    frozen 阻止普通字段重新赋值，slots 限制随意增加属性；对于这里的
    两个字符串字段，可把它理解为类似 Java record 的轻量数据载体。
    """

    document_id: str
    text: str


def _tokens(text: str) -> set[str]:
    """统一大小写并提取英文数字词，返回集合供交集计分使用。"""
    # 去重后统计重叠词数；这是英文词法基线，不衡量词频、中文分词或语义相似度。
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def rank_documents(
    query: str, documents: list[Document], limit: int
) -> list[Document]:
    """按重叠词数返回最多 limit 篇正分文档，分数相同则按标识排序。

    没有匹配词时返回空列表；调用者可以据此拒答或提示缺少依据，
    而不是把任意文档补入上下文。limit 小于 1 属于无效调用参数。
    """
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
