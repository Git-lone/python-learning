"""可解释的词项检索基线与有界对话记忆。

检索提供外部资料，对话窗口保留最近交流，两者解决不同的上下文问题。
本例没有向量库，也不调用模型生成答案；先观察检索排序与窗口淘汰，再接入完整 RAG。
"""

from collections import deque
from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class Document:
    """保存可追溯的文档标识与正文；标识既可用于稳定排序，也可用于后续引用来源。"""

    document_id: str
    text: str


def tokens(text: str) -> set[str]:
    """将英文文本切成去重词项；这是检索分词，不是大模型 SDK 的 token 编码。"""

    # set 忽略重复词，只衡量词项是否重叠；当前正则不处理中文，也没有语义理解。
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def retrieve(query: str, documents: list[Document], limit: int = 2) -> list[Document]:
    """按共同词数返回最多 limit 篇相关文档，无交集时返回空列表。

    分数相同按文档 ID 排序，让离线结果稳定可复现。调用方应传入非负 limit；
    这里保留 Python 切片的原始行为，尚未增加参数边界校验。
    """

    query_tokens = tokens(query)
    # 词项交集是可解释基线；后续可把本行替换为向量相似度。
    scored = [
        (len(query_tokens & tokens(document.text)), document.document_id, document)
        for document in documents
    ]
    return [
        document
        for score, _, document in sorted(scored, key=lambda item: (-item[0], item[1]))
        if score > 0
    ][:limit]


def main() -> int:
    """并列演示资料检索与最近两条对话保留，不将历史聊天当作外部事实库。"""

    documents = [
        Document("files", "Use with and pathlib to close a text file safely"),
        Document("async", "Use asyncio TaskGroup for concurrent tasks"),
        Document("tests", "Use pytest for automated tests"),
    ]
    top = retrieve("how to close a file", documents, limit=1)
    # maxlen 自动淘汰最旧消息；它限制的是消息条数，不是 token 总数。
    memory: deque[str] = deque(maxlen=2)
    memory.extend(["old", "user: close file", "assistant: use with"])
    # 当前固定问题必有命中文档；真实问答应先处理 top 为空，再决定拒答或补充查询。
    print(f"top={top[0].document_id} memory={len(memory)}")
    print(f"context={' | '.join(memory)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
