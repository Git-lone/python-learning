"""校验工具返回值而不是只判断 HTTP 成功。实现后运行本章验收；不要先复制参考答案。"""


def read_ticket(result: dict[str, object]) -> str:
    # 输入是含 isError/structuredContent 的协议字典，不是 SDK 对象。
    # 仅接受明确成功的 DEMO-1 工单及 waiting_for_customer 状态，否则抛 ValueError。
    raise NotImplementedError("Implement CH20-EX01")
