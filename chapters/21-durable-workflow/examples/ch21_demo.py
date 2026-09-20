import subprocess
import sys
from tempfile import TemporaryDirectory
from tools.course import ROOT

if __name__ == "__main__":
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
            # 子进程退出码非零才是执行失败；成功时读取 stdout 中的业务结果。
            if result.returncode:
                raise RuntimeError(result.stderr)
            print(result.stdout.strip())
