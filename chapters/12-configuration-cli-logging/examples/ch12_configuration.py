"""环境配置、结构化日志与显式依赖。"""

from collections.abc import Mapping
from dataclasses import dataclass
import io
import logging


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    environment: str
    log_level: int


def load_config(environ: Mapping[str, str]) -> RuntimeConfig:
    # 外部配置只在边界解析一次，内部代码始终接收合法类型。
    environment = environ.get("APP_ENV", "dev").strip() or "dev"
    level_name = environ.get("APP_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        raise ValueError(f"invalid log level: {level_name}")
    return RuntimeConfig(environment, level)


def main() -> int:
    config = load_config({"APP_ENV": "dev", "APP_LOG_LEVEL": "info"})
    stream = io.StringIO()
    # 示例使用独立 Logger，避免修改导入者的全局日志配置。
    logger = logging.Logger("course", config.log_level)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    logger.addHandler(handler)
    logger.info("service started")

    print(f"environment={config.environment} level={logging.getLevelName(config.log_level)}")
    print(f"log={stream.getvalue().strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
