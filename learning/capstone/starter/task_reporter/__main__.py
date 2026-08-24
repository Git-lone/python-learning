"""支持 ``python -m ...task_reporter``。"""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
