"""Checks the M1 exit rule (evals/scenarios/m1_exit_rule.yaml) on two eval runs.

  python -m evals.m1_exit_check <run1.json> <run2.json> <report stem>

Reads the rule (case, baseline, machine), the two run reports written by
evals/run_eval.py and the baseline report, and writes <report stem>.md with
each part of the rule and the verdict. It only reads reports: it runs nothing.
An earlier report is never overwritten.
"""

import json
import sys
from pathlib import Path

import yaml

RULE_FILE = Path("evals/scenarios/m1_exit_rule.yaml")


# Read a report .json file.
def load_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# Turns with verdict "fail" now that were not "fail" in the baseline.
def newly_failing(run: dict, baseline: dict) -> list[str]:
    before = {t["key"]: t["verdict"] for t in baseline["turns"]}
    return [t["key"] for t in run["turns"]
            if t["verdict"] == "fail" and before.get(t["key"]) != "fail"]


# The verdict of the rule's case in one run ("missing" if the run lacks it).
def case_verdict(run: dict, case: str) -> str:
    return next((t["verdict"] for t in run["turns"] if t["key"] == case), "missing")


# Check the rule. Returns (passed, report lines).
def check(rule: dict, runs: list[tuple[str, dict]], baseline: dict) -> tuple[bool, list[str]]:
    lines, passed = [], len(runs) == rule["runs"]
    for name, run in runs:
        on_machine = run["machine"].startswith(f"Machine: {rule['machine']} ")
        verdict, new = case_verdict(run, rule["case"]), newly_failing(run, baseline)
        ok = on_machine and verdict == "fixed" and not new
        passed = passed and ok
        lines += [f"## {name}", "", f"- {run['machine']}; commit {run['commit']}"
                  + (" (uncommitted changes)" if run.get("dirty") else ""),
                  f"- on the {rule['machine']}: {'yes' if on_machine else 'NO'}",
                  f"- {rule['case']}: {verdict} ({'ok' if verdict == 'fixed' else 'FAIL'})",
                  f"- newly failing against the baseline: {len(new)}",
                  *[f"  - {key}" for key in new], f"- this run: {'pass' if ok else 'FAIL'}", ""]
    return passed, lines


# Command line: check the rule on two runs and write the report.
def main() -> None:
    first, second, stem = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    md = stem.parent / f"{stem.name}.md"
    if md.exists():
        sys.exit(f"{md} already exists; earlier reports are never rewritten.")
    rule = yaml.safe_load(RULE_FILE.read_text(encoding="utf-8"))
    baseline = load_report(Path(rule["baseline"]))
    runs = [(p.as_posix(), load_report(p)) for p in (first, second)]
    passed, lines = check(rule, runs, baseline)
    head = [f"# M1 exit check: {'PASSED' if passed else 'NOT PASSED'}", "",
            (f"Rule: {RULE_FILE.as_posix()} (version {rule['version']}): {rule['case']} "
            f"fixed in all {rule['runs']} runs on the {rule['machine']}, and no turn newly "
            f"failing against {rule['baseline']} ({baseline['machine']}; commit "
            f"{baseline['commit']})."), ""]
    md.write_text("\n".join(head + lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{'PASSED' if passed else 'NOT PASSED'}; wrote {md}")


if __name__ == "__main__":
    main()
