"""Use chapter acceptance tests against either learner code or reference answers."""

import argparse
import subprocess
import sys

from tools.course import ROOT, run, selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solution", action="store_true")
    chapters = selected(parser)
    solution = "--solution" in sys.argv
    failures = 0
    for chapter in chapters:
        number = chapter["number"]
        directory = ROOT / chapter["directory"]
        targets = list((ROOT / "solutions").glob(f"ch{number:02d}_*.py"))
        if solution and len(targets) != 1:
            raise ValueError(f"CH{number:02d}: expected one reference answer, found {targets}")
        target = targets[0] if solution else directory / f"exercises/exercise_ch{number:02d}.py"
        try:
            result = run(
                [
                    "python",
                    "-m",
                    "pytest",
                    str(directory / "checks"),
                    "--override-ini=python_files=check_*.py",
                    "-q",
                ],
                timeout=60,
                target=target,
            )
            print(f"CH{number:02d} ({'solution' if solution else 'exercise'}):")
            print(result.stdout.strip())
            if result.returncode:
                print(result.stderr.strip())
                failures += 1
        except subprocess.TimeoutExpired:
            print(f"CH{number:02d}: TIMEOUT")
            failures += 1
    print(f"chapters: {len(chapters) - failures}/{len(chapters)} passed")
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
