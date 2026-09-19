"""pathlib、编码和上下文管理器。"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> int:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "orders.json"
        path.write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")
        with path.open(encoding="utf-8") as stream:
            orders = json.load(stream)
        print(f"loaded={len(orders)} file_closed={stream.closed}")
        print(f"suffix={path.suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
