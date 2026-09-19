import subprocess
import sys

from tools.course import ROOT


def test_real_stdio_server_process():
    result = subprocess.run(
        [sys.executable, "-m", "agent_lab.mcp_demo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "status=waiting_for_customer" in result.stdout
    assert "missing_ticket=handled" in result.stdout
