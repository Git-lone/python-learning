"""第 21 章最小演示：先在一个进程提交草稿，再在另一个进程恢复并批准。

两个进程共用临时 SQLite 文件，验证暂停状态确实离开了内存。阅读输出时应看到
先等待审批、后产生一条发布记录；具体的节点、checkpoint 和幂等账本见
agent_lab.durable。本脚本只跑正常审批路径，不等于已覆盖所有崩溃与并发场景。
"""

import subprocess
import sys
from tempfile import TemporaryDirectory
from tools.course import ROOT

if __name__ == "__main__":
    # 临时目录在本次演示结束后清理；它证明进程间恢复，不用于保留下一次启动的任务。
    with TemporaryDirectory() as directory:
        # 两个独立进程共用磁盘目录，证明恢复依赖 SQLite 检查点，而不是进程内变量。
        for action in ("start", "approve"):
            result = subprocess.run(
                # 用参数列表避免 shell 引号拼接，并复用当前虚拟环境的 Python。
                [sys.executable, "-m", "agent_lab.durable", action, "--directory", directory],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=20,
            )
            # 同步等待前一次命令结束后才执行下一次，确保审批发生在检查点写入之后。
            # 子进程退出码非零才是执行失败；成功时读取 stdout 中的业务结果。
            if result.returncode:
                raise RuntimeError(result.stderr)
            print(result.stdout.strip())
