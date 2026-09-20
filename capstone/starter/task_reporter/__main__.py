"""支持 ``python -m ...task_reporter``。"""

from .cli import main


if __name__ == "__main__":
    # 包入口只负责把 main 的返回值变成退出码，参数与业务逻辑留在可测试的模块中。
    raise SystemExit(main())
