"""pathlib、编码和上下文管理器。"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> int:
    # 外层 with 管理临时目录的生命周期，离开作用域后清理示例文件。
    with TemporaryDirectory() as directory:
        # Path 的 / 是路径拼接运算，不用手工处理 Windows 和 Unix 的分隔符。
        path = Path(directory) / "orders.json"
        path.write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")
        # 显式编码避免依赖机器默认值；即使 JSON 解析失败，文件也会关闭。
        with path.open(encoding="utf-8") as stream:
            orders = json.load(stream)
        print(f"loaded={len(orders)} file_closed={stream.closed}")
        print(f"suffix={path.suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
