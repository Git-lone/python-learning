"""Reference answer for CH21; inspect only after attempting the exercise."""

import sqlite3


def publish_once(database: str, request_id: str, body: str) -> str:
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
            saved = db.execute(
                "SELECT body FROM deliveries WHERE request_id=?", (request_id,)
            ).fetchone()
            # 幂等只允许同一键重放相同载荷；键相同但正文不同必须报冲突。
            if saved[0] != body:
                raise ValueError("idempotency key conflict")
        return "published:" + request_id
    finally:
        db.close()
