"""CH13-EX01 参考答案。"""

from collections.abc import Callable
import json


def load_json_with_retry(
    fetch: Callable[[], str], retries: int = 2
) -> dict[str, object]:
    if retries < 0:
        raise ValueError("retries must not be negative")
    for attempt in range(retries + 1):
        try:
            raw = fetch()
        except TimeoutError:
            # 只重试明确允许的瞬时错误；最后一次必须把原异常交给调用者。
            if attempt == retries:
                raise
            continue
        # 解析成功不代表结构有效，根节点仍需单独校验。
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("JSON root must be an object")
        return payload
    raise AssertionError("unreachable retry state")
