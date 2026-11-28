"""The checks every commit must pass: `ruff check .`, then `pytest` (AGENTS.md).

Run by the Git pre-commit hook (.githooks/pre-commit) with the project's
virtual-environment Python; can also be run by hand:
  .venv\\Scripts\\python.exe .githooks\\run_checks.py
Exits 1 (and Git refuses the commit) as soon as one check fails. The checks
run on the working tree, so unstaged changes are checked too.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKS = [("ruff check .", ["-m", "ruff", "check", "."]),
          ("pytest", ["-m", "pytest", "-q"])]


# Run each check in order; stop at the first failure. Returns the exit code.
def main() -> int:
    for name, args in CHECKS:
        print(f"pre-commit: {name}", flush=True)
        if subprocess.run([sys.executable, *args], cwd=ROOT, check=False).returncode != 0:
            print(f"pre-commit: {name} failed; commit refused.", flush=True)
            return 1
    print("pre-commit: ruff and pytest passed.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
