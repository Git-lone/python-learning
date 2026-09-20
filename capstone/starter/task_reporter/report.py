"""任务聚合与文本报告。"""

from collections.abc import Iterable, Sequence

from .model import Task


def completion_rate(tasks: Sequence[Task]) -> float:
    # 空任务集约定为 0%，同时避免除零；这属于业务约定而不是数学推导。
    if not tasks:
        return 0.0
    # done 已在输入边界校验为 bool，此处利用 True=1、False=0 进行计数。
    return sum(task.done for task in tasks) / len(tasks)


def pending_tasks(tasks: Iterable[Task]) -> Iterable[Task]:
    """按负责人和标题惰性产出未完成任务。"""
    # sorted 会先完整读取并排序，只有后续筛选和产出是惰性的，不是全流程流式处理。
    return (
        task
        for task in sorted(tasks, key=lambda item: (item.owner, item.title))
        if not task.done
    )


def render_report(tasks: Sequence[Task]) -> str:
    # 纯函数只返回字符串，不读文件、不打印，因此能直接针对内容做单元测试。
    completed = sum(task.done for task in tasks)
    lines = [
        "Task report",
        f"completed: {completed}/{len(tasks)} ({completion_rate(tasks):.1%})",
        "pending:",
    ]
    pending = list(pending_tasks(tasks))
    if not pending:
        lines.append("- none")
    else:
        lines.extend(
            f"- [{task.owner}] {task.title} ({task.estimate_minutes} min)"
            for task in pending
        )
    return "\n".join(lines)
