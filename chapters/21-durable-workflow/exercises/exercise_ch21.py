"""带载荷冲突校验的幂等发布。实现后运行本章验收；不要先复制参考答案。"""


def publish_once(database: str, request_id: str, body: str) -> str:
    # database 为 SQLite 文件路径；成功返回 published:<request_id>，记录需跨连接保留。
    # 重复键相同正文不新增记录，不同正文及空键/空正文报 ValueError；注意关闭连接。
    raise NotImplementedError("Implement CH21-EX01")
