"""练习：为可重试的数据获取边界增加 JSON 校验。"""

from collections.abc import Callable


def load_json_with_retry(
    fetch: Callable[[], str], retries: int = 2
) -> dict[str, object]:
    """只重试 TimeoutError，并要求响应 JSON 根节点为对象。"""
    # TODO：重试次数表示“首次尝试之后还能再试几次”。
    # JSONDecodeError、业务 ValueError 等不可恢复错误不得重试。
    raise NotImplementedError("请完成 CH13-EX01")
