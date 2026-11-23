"""把模型的 JSON 建议送过输入合同、允许列表和工具参数三道边界。

固定文本代替模型响应，便于重复观察错误；这里没有调用真实 LLM。
复用入门示例的注册表和 add，只开放纯计算能力，不读写文件、数据库或网络。
"""

import argparse
import json

from ch15_tools import ToolRegistry, UnknownToolError, add


CASES = {
    "success": '{"name":"add","arguments":{"left":2,"right":3}}',
    "bad-parameters": '{"name":"add","arguments":{"left":true,"right":3}}',
    "unknown-tool": '{"name":"delete_order","arguments":{"order_id":"SO-1"}}',
    "invalid-structure": '[]',
    "invalid-json": 'not-json',
    "invalid-arguments": '{"name":"add","arguments":[2,3]}',
}


def parse_tool_call(raw: str) -> tuple[str, dict[str, object]]:
    """解析一个调用建议，返回工具名和参数对象；不猜测、补全或执行动作。

    类似 Java 接收外部 JSON 后校验请求 DTO。Python 的类型标注不会在运行时
    阻止 list、None 等值传入，因此这里仍要逐项检查真正解码出的对象。
    """

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("invalid JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("tool call must be a JSON object")
    # 本例合同只接受 name 和 arguments；多出的顶层指令也不隐式获得执行权。
    if set(payload) != {"name", "arguments"}:
        raise ValueError("tool call requires exactly name and arguments")
    name = payload["name"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    arguments = payload["arguments"]
    if not isinstance(arguments, dict):
        raise ValueError("arguments must be a JSON object")
    return name, arguments


def run_suggestion(registry: ToolRegistry, raw: str) -> dict[str, object]:
    """为本例的 add 调用生成成功或拒绝观察；拒绝不会变成伪造的成功结果。"""

    try:
        name, arguments = parse_tool_call(raw)
    except ValueError as error:
        return {"status": "rejected", "stage": "request-contract", "reason": str(error)}

    try:
        result = registry.execute(name, arguments)
    except UnknownToolError as error:
        # 只拦截分派层的专用异常；处理器内部的 KeyError 应暴露为程序问题。
        return {"status": "rejected", "stage": "allowlist", "reason": str(error.args[0])}
    except ValueError as error:
        # 此时已进入 add，但参数校验在加法之前失败，并没有产生计算结果。
        # 这个分类基于本例唯一工具 add 的约定；新工具应定义明确的参数异常。
        return {"status": "rejected", "stage": "tool-parameters", "reason": str(error)}
    return {"status": "ok", "tool": name, "result": result}


def main() -> int:
    """默认运行所有固定案例，也可用 --case 单独核对一条输入。"""

    parser = argparse.ArgumentParser(description="观察工具建议在哪道边界被接受或拒绝")
    parser.add_argument("--case", choices=["all", *CASES], default="all")
    options = parser.parse_args()
    registry = ToolRegistry()
    # 允许列表由应用配置，模型不能借名字注册新函数。add 无外部 I/O，因而本例
    # 只开放无写副作用的计算；注册表本身不会自动判断一个函数是否只读。
    registry.register("add", add)
    selected = CASES if options.case == "all" else {options.case: CASES[options.case]}
    for case_name, raw in selected.items():
        observation = run_suggestion(registry, raw)
        print(f"case={case_name} {json.dumps(observation, ensure_ascii=False)}")
    # “拒绝反例”也是预期演示结果，进程成功退出不代表每个建议都获准执行。
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
