"""第 21 章持久化工作流：草稿暂停审批，跨进程恢复，再幂等写入本地业务账本。

阅读顺序是 State → Ledger → build_graph → inspect_workflow → main。checkpoints.sqlite 保存流程
进度，ledger.sqlite 保存模拟发布结果，二者职责与事务边界不同。本例不调用模型、
不向外部系统发消息；“发布”仅是 SQLite 插入，不能据此宣称远程写入恰好执行一次。
"""

from __future__ import annotations

import argparse
from contextlib import closing, contextmanager
from collections.abc import Iterator
from pathlib import Path
import sqlite3
from typing import Any, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict, total=False):
    """图节点共享的状态形状，类似 Java 状态 DTO，但运行时仍是普通字典。"""

    # total=False 允许节点只返回更新字段；TypedDict 本身不做运行时数据校验。
    request_id: str
    draft: str
    approved: bool
    result: str


class Ledger:
    """以 request_id 为唯一键的本地发布账本，演示业务副作用如何抵御重放。

    同一请求、相同正文重复发布会复用已有结果；同一请求换了正文则报错。
    数据库唯一键承担去重，不能仅靠进程内布尔标记，因为进程重启会丢失内存状态。
    """

    def __init__(self, path: Path) -> None:
        """记录数据库位置并确保表存在；不清空已有账本，以便后续进程继续使用。"""

        self.path = path
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS deliveries "
                "(request_id TEXT PRIMARY KEY, body TEXT NOT NULL)"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """提供短事务连接，类似 try-with-resources 加提交/回滚的组合。

        @contextmanager 将单次 yield 的生成器变成 with 资源管理器；连接不是
        长驻的共享会话。SQLite 的 timeout=5 是等待锁的时间，不是整个流程超时。
        """

        # yield 把连接交给 with 的调用方；正常退出提交，异常回滚，最后始终关闭。
        # sqlite3.Connection 的 with 只管事务，不会自动 close。
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def publish(self, request_id: str, body: str) -> str:
        """提交一次模拟发布；重复请求可以重放，幂等键与正文冲突则拒绝。

        INSERT OR IGNORE 只解决重复插入，随后的正文比较才防止错误复用幂等键。
        这里没有对远程服务做事务承诺；真实外部发布还需对方支持幂等或另做补偿。
        """

        if not request_id or not body:
            raise ValueError("request_id and body are required")
        # 唯一键与载荷校验放在同一业务事务中；重复键只允许重放相同正文。
        with self._connect() as db:
            # 使用参数绑定，不把 request_id 或正文拼接进 SQL。
            db.execute("INSERT OR IGNORE INTO deliveries VALUES (?, ?)", (request_id, body))
            saved = db.execute(
                "SELECT body FROM deliveries WHERE request_id=?", (request_id,)
            ).fetchone()
            if saved is None or saved[0] != body:
                raise ValueError("idempotency key reused with different payload")
        return f"published:{request_id}"

    def count(self) -> int:
        """返回账本中的唯一发布数量，用来观察重放是否产生重复记录。"""

        with self._connect() as db:
            return int(db.execute("SELECT count(*) FROM deliveries").fetchone()[0])


def build_graph(checkpointer: SqliteSaver, ledger: Ledger) -> Any:
    """组装审批、发布两个节点，并把流程持久化交给传入的 checkpointer。

    节点返回状态增量，框架负责合并和记录进度。checkpointer 使流程可恢复，
    ledger 使副作用可重放；这两项能力需要分别实现，不能把检查点当成业务事务。
    """

    def approve(state: State) -> State:
        # 审批节点把待确认内容交给调用方，恢复值必须严格为布尔值，避免字符串 "false" 等歧义。
        # interrupt 保存暂停点；恢复时节点可能重新执行，因此之前不要放不可重放副作用。
        answer = interrupt({"request_id": state["request_id"], "draft": state["draft"]})
        if not isinstance(answer, bool):
            raise ValueError("approval must be a boolean")
        return {"approved": answer}

    def publish(state: State) -> State:
        # 拒绝仍会进入该节点，但只写回 rejected 状态，不插入发布账本。
        # 检查点与业务写入不在同一事务；发布后若保存状态失败，重放靠 ledger 幂等兜底。
        result = (
            ledger.publish(state["request_id"], state["draft"]) if state["approved"] else "rejected"
        )
        return {"result": result}

    graph = StateGraph(State)
    graph.add_node("approve", approve)
    graph.add_node("publish", publish)
    graph.add_edge(START, "approve")
    graph.add_edge("approve", "publish")
    graph.add_edge("publish", END)
    return graph.compile(checkpointer=checkpointer)


def inspect_workflow(directory: Path, thread: str) -> dict[str, object]:
    """观察已有检查点与账本，不构建或执行图，也不创建缺失的数据库。

    使用只读 SQLite 连接和 checkpointer 的读取接口。两份文件分别读取，结果适合
    本地串行实验；它不是并发执行期间跨数据库的一致性快照。
    """

    checkpoint_path = directory / "checkpoints.sqlite"
    ledger_path = directory / "ledger.sqlite"
    for path in (checkpoint_path, ledger_path):
        if not path.is_file():
            raise FileNotFoundError(f"database file not found: {path}")

    # mode=ro 同时防止误建文件和写入；已存在数据库由正常 start 命令完成过初始化。
    with closing(sqlite3.connect(checkpoint_path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        checkpoint = SqliteSaver(db).get_tuple({"configurable": {"thread_id": thread}})
        values = checkpoint.checkpoint["channel_values"] if checkpoint else {}

    # 按状态中的业务 request_id 查账本，不假定所有调用者都像 CLI 一样令它等于 thread。
    request_id = values.get("request_id")
    with closing(sqlite3.connect(ledger_path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        total = db.execute("SELECT count(*) FROM deliveries").fetchone()[0]
        # 缺少检查点时无法确定业务键，用 None 表示未知，不把“无法关联”当作零条发布。
        current = (
            db.execute(
                "SELECT count(*) FROM deliveries WHERE request_id=?", (request_id,)
            ).fetchone()[0]
            if request_id is not None
            else None
        )
    return {
        "checkpoint_found": checkpoint is not None,
        "request_id": request_id,
        "approved": values.get("approved"),
        "result": values.get("result"),
        "deliveries_total": total,
        "deliveries_for_request": current,
    }


def main() -> None:
    """以命令行模拟提交人和审批人的两次操作，每次启动都从磁盘读取同一流程。

    start 新建并暂停，approve/reject 用 Command 恢复已有暂停点，inspect 只观察。
    本例未实现审批人身份认证或多工作进程协调，这些不能由持久化检查点自动获得。
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "approve", "reject", "inspect"])
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--thread", default="demo-thread")
    args = parser.parse_args()
    if args.action == "inspect":
        try:
            observation = inspect_workflow(args.directory, args.thread)
        except FileNotFoundError as error:
            parser.error(str(error))
        for key, value in observation.items():
            print(f"{key}={value}")
        return

    args.directory.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(args.directory / "ledger.sqlite")
    # 相同 thread_id 定位同一次工作流；更换 ID 是新任务，不是恢复旧任务。
    config = {"configurable": {"thread_id": args.thread}}
    with SqliteSaver.from_conn_string(str(args.directory / "checkpoints.sqlite")) as saver:
        graph = build_graph(saver, ledger)
        state = graph.get_state(config)
        if args.action == "start":
            if state.values:
                parser.error("thread already exists; resume it or choose a new --thread")
            result = graph.invoke({"request_id": args.thread, "draft": "Synthetic reply"}, config)
        else:
            if not state.next:
                parser.error("thread has no pending approval")
            # resume 的布尔值成为 interrupt 的返回值，而不是重新提交初始输入。
            result = graph.invoke(Command(resume=args.action == "approve"), config)
        print("waiting_approval" if result.get("__interrupt__") else result["result"])
        print(f"deliveries={ledger.count()}")


if __name__ == "__main__":
    main()
