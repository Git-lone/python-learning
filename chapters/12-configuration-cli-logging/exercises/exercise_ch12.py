"""练习：把不可信环境变量转换为强类型配置。"""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    host: str
    port: int
    debug: bool


def load_settings(environ: Mapping[str, str]) -> Settings:
    """读取 APP_HOST、APP_PORT、APP_DEBUG，并校验端口与布尔值。"""
    # TODO 1：应用默认值并去除字符串两端空白。
    # TODO 2：把端口转换为 int，把 debug 严格转换为 bool。
    # TODO 3：任何非法值都在此处抛出 ValueError。
    raise NotImplementedError("请完成 CH12-EX01")
