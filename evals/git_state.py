"""The commit line of every check-script and eval report (measuring tool).

git_state() gives the short HEAD commit, plus " (uncommitted changes present)"
when the working tree has changes. Changed or untracked files under
evals/reports/ do not count (M1 cleanup measuring fix): a run writes its own
reports there, so the run after it would otherwise always look dirty
(M1 cleanup temperature runs). eval_compare.code_changed ignores the same
folder. Any other changed or untracked file still counts.
"""

import subprocess

REPORTS = "evals/reports/"


# The paths in `git status --porcelain` output that lie outside evals/reports/.
def outside_reports(porcelain: str) -> list[str]:
    paths = []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        for path in line[3:].split(" -> "):             # a rename names both paths
            path = path.strip('"')
            if not path.startswith(REPORTS):
                paths.append(path)
    return paths


# "<commit>" or "<commit> (uncommitted changes present)".
def git_state() -> str:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          check=False, capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain"],
                            check=False, capture_output=True, text=True).stdout
    return head + (" (uncommitted changes present)" if outside_reports(status) else "")
