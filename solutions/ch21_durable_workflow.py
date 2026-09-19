"""Reference answer for CH21; inspect only after attempting the exercise."""

import sqlite3


def publish_once(database: str, request_id: str, body: str) -> str:
    if not request_id or not body:
        raise ValueError("request_id and body are required")
    db = sqlite3.connect(database)
    try:
        with db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS deliveries "
                "(request_id TEXT PRIMARY KEY, body TEXT NOT NULL)"
            )
            db.execute("INSERT OR IGNORE INTO deliveries VALUES (?, ?)", (request_id, body))
            saved = db.execute(
                "SELECT body FROM deliveries WHERE request_id=?", (request_id,)
            ).fetchone()
            if saved[0] != body:
                raise ValueError("idempotency key conflict")
        return "published:" + request_id
    finally:
        db.close()
