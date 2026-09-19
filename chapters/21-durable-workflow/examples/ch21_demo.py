import subprocess
import sys
from tempfile import TemporaryDirectory
from tools.course import ROOT

if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        for action in ("start", "approve"):
            result = subprocess.run(
                [sys.executable, "-m", "agent_lab.durable", action, "--directory", directory],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=20,
            )
            if result.returncode:
                raise RuntimeError(result.stderr)
            print(result.stdout.strip())
