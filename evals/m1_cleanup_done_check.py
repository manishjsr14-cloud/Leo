"""Checks the M1 cleanup done rule (IMPLEMENTATION_PLAN.md, M1 cleanup) on one run.

  python -m evals.m1_cleanup_done_check <run.json> <report stem>

Rule, agreed before the run: after all cleanup items, a full eval suite run
on the laptop shows no newly failing turn against BASELINE, judged with
scorer v2 on both sides (the baseline's stored replies rescored with v2);
the v1 result is reported alongside. It only reads reports: it runs nothing.
An earlier report is never overwritten.
"""

import json
import sys
from pathlib import Path

from evals.eval_compare import newly_failing, with_v2_report

BASELINE = Path("evals/reports/m1.10_eval_2026-11-23_run1.json")
MACHINE = "laptop"


# Read a report .json file, scored with v2 too.
def load(path: Path) -> dict:
    return with_v2_report(json.loads(path.read_text(encoding="utf-8")))


# Check the rule. Returns (passed, report lines).
def check(run: dict, baseline: dict) -> tuple[bool, list[str]]:
    old = {t["key"]: t for t in baseline["turns"]}
    new = {t["key"]: t for t in run["turns"]}
    v1, v2 = newly_failing(old, new, "v1"), newly_failing(old, new, "v2")
    on_machine = run["machine"].startswith(f"Machine: {MACHINE} ")
    passed = on_machine and not v2 and not run.get("dirty")
    lines = [f"- {run['machine']}; commit {run['commit']}"
             + (" (uncommitted changes)" if run.get("dirty") else ""),
             f"- on the {MACHINE}: {'yes' if on_machine else 'NO'}",
             f"- newly failing, scorer v2 on both sides (the rule): {len(v2)}", *v2,
             f"- newly failing, scorer v1 (reported alongside): {len(v1)}", *v1]
    return passed, lines


# Command line: check the rule on one run and write the report.
def main() -> None:
    run_path, stem = Path(sys.argv[1]), Path(sys.argv[2])
    md = stem.parent / f"{stem.name}.md"
    if md.exists():
        sys.exit(f"{md} already exists; earlier reports are never rewritten.")
    baseline = load(BASELINE)
    passed, lines = check(load(run_path), baseline)
    head = [f"# M1 cleanup done check: {'PASSED' if passed else 'NOT PASSED'}", "",
            (f"Rule (IMPLEMENTATION_PLAN.md, M1 cleanup): no turn newly failing against "
             f"{BASELINE.as_posix()} ({baseline['machine']}; commit {baseline['commit']}), "
             "scorer v2 on both sides, on a committed tree on the laptop."), "",
            f"Run: {run_path.as_posix()}", ""]
    md.write_text("\n".join(head + lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{'PASSED' if passed else 'NOT PASSED'}; wrote {md}")


if __name__ == "__main__":
    main()
