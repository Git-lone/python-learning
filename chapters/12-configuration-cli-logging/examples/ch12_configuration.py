"""环境配置、格式化日志与显式依赖；本例日志为普通文本，不是 JSON 日志。"""

from collections.abc import Mapping
from dataclasses import dataclass
import io
import logging


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """保存解析后的环境名称与数字日志级别，供应用直接使用。"""

    environment: str
    log_level: int


def load_config(environ: Mapping[str, str]) -> RuntimeConfig:
    """解析配置映射，缺省环境为 dev、日志级别为 INFO，非法级别抛 ValueError。

    这是显式构造配置对象的示例，没有依赖 Java/Spring 式自动配置注入。
    环境名称去除首尾空白，空值回退为 dev，没有限定为某一组部署环境。
    """

    # 注入 Mapping 而不直接读取 os.environ，测试可传普通字典且不污染进程环境。
    # 外部配置只在边界解析一次，内部代码始终接收合法类型。
    environment = environ.get("APP_ENV", "dev").strip() or "dev"
    level_name = environ.get("APP_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        raise ValueError(f"invalid log level: {level_name}")
    return RuntimeConfig(environment, level)


def main() -> int:
    config = load_config({"APP_ENV": "dev", "APP_LOG_LEVEL": "info"})
    # StringIO 是内存文本流，便于断言日志内容，无需创建或清理日志文件。
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
