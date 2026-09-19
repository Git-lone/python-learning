"""CH07-EX01 参考答案。"""

from pathlib import Path


def count_non_blank_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as stream:
        return sum(1 for line in stream if line.strip())
