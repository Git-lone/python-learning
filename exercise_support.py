"""练习检查文件共用的动态加载工具。"""

from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import sys
from types import ModuleType

TARGET_ENV = "PYTHON_TUTORIAL_TARGET"


def load_target(check_file: str) -> ModuleType:
    """加载当前章节练习，或由检查器指定的参考答案。"""
    check_path = Path(check_file).resolve()
    configured = os.environ.get(TARGET_ENV)
    if configured:
        source = Path(configured).resolve()
    else:
        chapter_id = check_path.stem.removeprefix("check_")
        source = check_path.parents[1] / "exercises" / f"exercise_{chapter_id}.py"
    if not source.is_file():
        raise ImportError(f"练习目标不存在：{source}")

    module_name = f"_python_tutorial_{source.stem}_{abs(hash(source))}"
    spec = spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法创建练习模块：{source}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
