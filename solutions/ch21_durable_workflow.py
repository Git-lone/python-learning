"""第 21 章参考解答：用持久化记录约束同一请求的重复执行。

请先独立完成练习再阅读。本题用数据库记录模拟发布结果，练习幂等键与
载荷冲突；它不包含审批快照、工作流续跑或真实的外部发布接口。
"""

import sqlite3


def publish_once(database: str, request_id: str, body: str) -> str:
    """保存发布请求；相同请求和正文可重放，改用不同正文则拒绝。

    database 是 SQLite 数据库路径，request_id 是调用方为同一次业务操作
    保持不变的标识。成功时返回带该标识的发布结果，缺参或载荷冲突时抛出
    ValueError。文件型数据库能保留跨连接的记录；使用 :memory: 则不能在
    下次调用中恢复这些记录。

    这里的原子性只覆盖本地数据库写入。若扩展为真实发布，还需要处理
    外部服务已执行但本地尚未记账的窗口，不能据此宣称外部操作严格一次。
    """
    if not request_id or not body:
        raise ValueError("request_id and body are required")
    db = sqlite3.connect(database)
    try:
        # 连接的 with 管理提交/回滚，不负责关闭连接，因此仍需要下面的 finally。
        with db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS deliveries "
                "(request_id TEXT PRIMARY KEY, body TEXT NOT NULL)"
            )
            # 唯一键处理重复请求；? 参数绑定避免把用户输入拼接成 SQL。
            db.execute("INSERT OR IGNORE INTO deliveries VALUES (?, ?)", (request_id, body))
            # 重放时读取的是首次保存的正文，以它核验本次请求，而不覆盖历史载荷。
            saved = db.execute(
                "SELECT body FROM deliveries WHERE request_id=?", (request_id,)
            ).fetchone()
            # 幂等只允许同一键重放相同载荷；键相同但正文不同必须报冲突。
            if saved[0] != body:
                raise ValueError("idempotency key conflict")
        # 离开事务后才返回成功；提交失败会抛出异常，不会产生这条成功结果。
        return "published:" + request_id
    finally:
        db.close()
