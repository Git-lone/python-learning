"""可解释的词项检索基线与有界对话记忆。"""

from collections import deque
from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class Document:
    document_id: str
    text: str


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def retrieve(query: str, documents: list[Document], limit: int = 2) -> list[Document]:
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
    documents = [
        Document("files", "Use with and pathlib to close a text file safely"),
        Document("async", "Use asyncio TaskGroup for concurrent tasks"),
        Document("tests", "Use pytest for automated tests"),
    ]
    top = retrieve("how to close a file", documents, limit=1)
    # maxlen 自动淘汰最旧消息，防止上下文无限增长。
    memory: deque[str] = deque(maxlen=2)
    memory.extend(["old", "user: close file", "assistant: use with"])
    print(f"top={top[0].document_id} memory={len(memory)}")
    print(f"context={' | '.join(memory)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
