"""CH12-EX01 参考答案。"""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    host: str
    port: int
    debug: bool


def load_settings(environ: Mapping[str, str]) -> Settings:
    # 显式注入配置来源，让单元测试无需修改进程环境变量。
    # 先校验主机，避免空字符串进入网络层后才产生难懂错误。
    host = environ.get("APP_HOST", "127.0.0.1").strip()
    if not host:
        raise ValueError("APP_HOST must not be empty")
    try:
        port = int(environ.get("APP_PORT", "8000"))
    except ValueError as error:
        raise ValueError("APP_PORT must be an integer") from error
    # 转换成功和范围合法是两件事；例如 "70000" 能转 int，但不是有效服务端口。
    if not 1 <= port <= 65535:
        raise ValueError("APP_PORT must be between 1 and 65535")
    # 不使用 bool(raw_string)：bool("false") 仍然是 True。
    raw_debug = environ.get("APP_DEBUG", "false").strip().lower()
    if raw_debug not in {"true", "false"}:
        raise ValueError("APP_DEBUG must be true or false")
    return Settings(host, port, raw_debug == "true")
