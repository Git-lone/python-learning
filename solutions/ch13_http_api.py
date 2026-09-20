"""CH13-EX01 参考答案。"""

from collections.abc import Callable
import json


def load_json_with_retry(
    fetch: Callable[[], str], retries: int = 2
) -> dict[str, object]:
    if retries < 0:
        raise ValueError("retries must not be negative")
    # retries 不包含首次尝试，所以 0 表示仍会调用一次 fetch。
    for attempt in range(retries + 1):
        try:
            raw = fetch()
        except TimeoutError:
            # 只重试明确允许的瞬时错误；最后一次必须把原异常交给调用者。
            if attempt == retries:
                raise
            continue
        # 解析放在超时捕获范围外：JSON 格式错误不属于本练习允许重试的错误类型。
        # 解析成功不代表结构有效，根节点仍需单独校验。
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("JSON root must be an object")
        return payload
    raise AssertionError("unreachable retry state")
