"""任务聚合与文本报告。"""

from collections.abc import Iterable, Sequence

from .model import Task


def completion_rate(tasks: Sequence[Task]) -> float:
    if not tasks:
        return 0.0
    return sum(task.done for task in tasks) / len(tasks)


def pending_tasks(tasks: Iterable[Task]) -> Iterable[Task]:
    """按负责人和标题惰性产出未完成任务。"""
    return (
        task
        for task in sorted(tasks, key=lambda item: (item.owner, item.title))
        if not task.done
    )


def render_report(tasks: Sequence[Task]) -> str:
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
