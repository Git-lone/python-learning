"""CH07-EX01 参考答案。"""

from pathlib import Path


def count_non_blank_lines(path: Path) -> int:
    # return 离开 with 前仍会关闭文件；不捕获 I/O 异常，交给调用方决定处理方式。
    with path.open(encoding="utf-8") as stream:
        # 逐行读取避免一次加载整个文件；仅包含空格、制表符或换行的行也算空行。
        return sum(1 for line in stream if line.strip())
