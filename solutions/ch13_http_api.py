"""CH13-EX01 参考答案：分开处理获取响应、超时重试和 JSON 结构校验。

通过注入 fetch 隔离网络访问，练习可以用本地函数模拟响应或超时，
无需启动 HTTP 服务；本模块本身没有绑定具体的 HTTP 客户端。
"""

from collections.abc import Callable
import json


def load_json_with_retry(
    fetch: Callable[[], str], retries: int = 2
) -> dict[str, object]:
    """调用无参数的 fetch 获取 JSON 文本，成功时返回 JSON 对象字典。

    retries 表示首次请求之外的重试次数，仅捕获 Python 的 TimeoutError。
    调用者需确认 fetch 的操作可以安全重试；这里不处理退避或业务幂等。
    其他获取异常、解析错误及非对象根节点都会直接交给调用者处理。
    """
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
    # 正常控制流必定已返回或抛错；此处表达循环应有的后置条件。
    raise AssertionError("unreachable retry state")
