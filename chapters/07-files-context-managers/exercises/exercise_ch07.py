"""练习：安全读取 UTF-8 文本文件。"""

from pathlib import Path


def count_non_blank_lines(path: Path) -> int:
    """统计非空行；必须使用上下文管理器和显式 UTF-8 编码。"""
    # 只有空格或制表符的行也算空行；不要把读取失败伪装成有效的零行结果。
    raise NotImplementedError("请完成 CH07-EX01")
