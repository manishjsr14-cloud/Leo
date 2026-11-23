"""Compare two M1.10 eval reports (their .json files): each metric before and
after, every turn whose verdict changed, and the newly failing turns.

  python -m evals.eval_compare <before.json> <after.json>

When the two runs are on different machines, routing, tool-call, reply-check,
refused-call and LLM-call metrics are still compared, but timing rows are left
out: only timings depend on the machine.
When no file outside evals/reports/ changed between the two commits (and both
trees were clean), the comparison is labelled a noise check: any difference
is model noise, not a code change.
"""

import json
import subprocess
import sys
from pathlib import Path

from evals.eval_metrics import GROUPS, TIMING_ROWS, number_text, rate_text


# True if code changed between two commits, False if only reports did,
# None if it cannot be told (a dirty tree or git failed).
def code_changed(before: dict, after: dict) -> bool | None:
    if before["dirty"] or after["dirty"]:
        return None
    out = subprocess.run(["git", "diff", "--name-only", before["commit"], after["commit"]],
                         check=False, capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return any(not name.startswith("evals/reports/") for name in out.stdout.split())


# The label line for the comparison.
def label(before: dict, after: dict) -> str:
    changed = code_changed(before, after)
    if changed is False:
        return ("**Noise check:** no file outside evals/reports/ changed between "
                f"{before['commit']} and {after['commit']}, so every difference below is model noise.")
    if changed is None:
        return "Code change between the runs: unknown (uncommitted changes or git failed)."
    return f"Code changed between {before['commit']} and {after['commit']}."


# Metric rows "| metric | group | before | after |", timing rows only on one machine.
def metric_rows(before: dict, after: dict, same_machine: bool) -> list[str]:
    rows = ["| metric | group | before | after |", "|---|---|---|---|"]
    for kind, show in (("rates", rate_text), ("numbers", number_text)):
        for name, cells in after["metrics"][kind].items():
            if name in TIMING_ROWS and not same_machine:
                continue
            old = before["metrics"][kind].get(name, {})
            rows += [f"| {name} | {g} | {show(old[g]) if g in old else '-'} | {show(cells[g])} |"
                     for g in GROUPS]
    return rows


# Lines comparing two reports (loaded .json dicts).
def compare(before: dict, after: dict, before_name: str, after_name: str) -> list[str]:
    same_machine = before["machine"] == after["machine"]
    lines = [f"Before: {before_name} ({before['machine']}; commit {before['commit']})",
             f"After: {after_name} ({after['machine']}; commit {after['commit']})", "",
             label(before, after), ""]
    if not same_machine:
        lines += ["The machines differ, so timing rows (" + ", ".join(sorted(TIMING_ROWS))
                  + ") are left out; the other metrics do not depend on the machine.", ""]
    lines += metric_rows(before, after, same_machine) + [""]
    old = {t["key"]: t for t in before["turns"]}
    new = {t["key"]: t for t in after["turns"]}
    changed = [f"- {k}: {old[k]['verdict']} -> {new[k]['verdict']}"
               for k in new if k in old and old[k]["verdict"] != new[k]["verdict"]]
    failing = [f"- {k}: {'; '.join(new[k]['tool_fails'] + new[k]['reply_fails']) or 'routing'}"
               for k in new if new[k]["verdict"] == "fail"
               and old.get(k, {}).get("verdict") != "fail"]
    lines += [f"Turns whose verdict changed: {len(changed)}", "", *(changed or ["- none"]), "",
              f"Newly failing turns: {len(failing)}", "", *(failing or ["- none"])]
    only = sorted(set(old) ^ set(new))
    if only:
        lines += ["", "Turns in only one report: " + ", ".join(only)]
    return lines


# Command line: print the comparison of two report .json files.
def main() -> None:
    before_path, after_path = Path(sys.argv[1]), Path(sys.argv[2])
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = json.loads(after_path.read_text(encoding="utf-8"))
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(compare(before, after, str(before_path), str(after_path))))


if __name__ == "__main__":
    main()
