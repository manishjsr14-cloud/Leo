"""M1 cleanup item 7: compare eval runs at two temperatures, all on one commit.

  python -m evals.m1_cleanup_temperature_compare <out.md> <baseline.json> <run.json>...

Reads report .json files written by evals/run_eval.py (each records the
temperature in its sampling line) and the M1.10 baseline, and writes:
  - per run: turns passing all checks (v1 and v2), all / Hinglish / English,
    LLM calls per turn and turn seconds (same machine only);
  - verdict flips between the two runs at the same temperature (noise);
  - turns whose v2 verdict differs between the temperatures;
  - newly failing turns against the baseline, v1 and v2 on both sides.
It also lists each run's commit and recorded tree state ("uncommitted changes
present"), and the files that differ between the commits the runs recorded.
It only reads reports and git; the recommendation is written by hand after it.
"""

import json
import re
import subprocess
import sys
from itertools import pairwise
from pathlib import Path

from evals.eval_compare import newly_failing, with_v2_report
from evals.eval_metrics import rate_text


# Read one report and score it with v2 too.
def load(path: Path) -> dict:
    return with_v2_report(json.loads(path.read_text(encoding="utf-8")))


# The temperature a report's sampling line says was sent.
def temperature(report: dict) -> str:
    found = re.search(r"set temperature ([\d.]+)", report["sampling"])
    return found.group(1) if found else "?"


# Keys whose `field` verdict differs between two reports.
def flips(a: dict, b: dict, field: str = "verdict_v2") -> list[str]:
    old = {t["key"]: t[field] for t in a["turns"]}
    return [f"{t['key']}: {old[t['key']]} -> {t[field]}" for t in b["turns"]
            if t["key"] in old and old[t["key"]] != t[field]]


# One table row for one run.
def row(name: str, r: dict) -> str:
    rates, nums = r["metrics"]["rates"], r["metrics"]["numbers"]
    v1, v2 = rates["turn passed (all checks)"], rates["turn passed (all checks, scorer v2)"]
    cells = [rate_text(v1[g]) for g in ("all", "hinglish", "en")]
    cells += [rate_text(v2[g]) for g in ("all", "hinglish", "en")]
    calls, secs = nums["LLM calls per turn"]["all"], nums["turn seconds"]["all"]
    return (f"| {name} | {temperature(r)} | {r['commit']} | " + " | ".join(cells)
            + f" | {calls['avg']:.2f} | {secs['avg']:.1f} |")


# Lines on each run's commit and recorded tree state, and the files that differ
# between the commits the runs recorded (git diff --name-only).
def commits(runs: list[tuple[str, dict]]) -> list[str]:
    lines = [f"- {name}: commit {r['commit']}"
             + (" (recorded 'uncommitted changes present')" if r.get("dirty") else " (clean)")
             for name, r in runs]
    seen = list(dict.fromkeys(r["commit"] for _, r in runs))
    for a, b in pairwise(seen):
        out = subprocess.run(["git", "diff", "--name-only", a, b],
                             check=False, capture_output=True, text=True)
        files = out.stdout.split() if out.returncode == 0 else ["(git diff failed)"]
        lines.append(f"- files changed between {a} and {b}: " + (", ".join(files) or "none"))
    return lines


# Build the report lines.
def report(baseline: tuple[str, dict], runs: list[tuple[str, dict]]) -> list[str]:
    lines = ["# M1 cleanup temperature comparison", "",
             "Machines: " + "; ".join(sorted({r["machine"] for _, r in runs})), "",
             (f"Baseline: {baseline[0]} ({baseline[1]['machine']}; commit "
              f"{baseline[1]['commit']}; {baseline[1]['sampling'][:60]}...)"), "",
             "## Commits and tree state", "", *commits(runs), "",
             "## Pass rates", "",
             ("| run | temp | commit | v1 all | v1 hinglish | v1 en | v2 all | v2 hinglish | "
              "v2 en | LLM calls/turn avg | turn s avg |"),
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    lines += [row(name, r) for name, r in runs]
    by_temp: dict[str, list[tuple[str, dict]]] = {}
    for name, r in runs:
        by_temp.setdefault(temperature(r), []).append((name, r))
    lines += ["", "## Verdict flips between runs at the same temperature (noise)", ""]
    for temp, group in by_temp.items():
        for (na, a), (nb, b) in pairwise(group):
            for field in ("verdict", "verdict_v2"):
                found = flips(a, b, field)
                lines.append(f"- {temp}: {na} -> {nb}, {field}: {len(found)}"
                             + "".join(f"\n  - {f}" for f in found))
    temps = list(by_temp)
    if len(temps) == 2:
        lines += ["", f"## Turns whose v2 verdict differs between {temps[0]} and {temps[1]}", ""]
        for (na, a) in by_temp[temps[0]]:
            for (nb, b) in by_temp[temps[1]]:
                found = flips(a, b)
                lines.append(f"- {na} vs {nb}: {len(found)}" + "".join(f"\n  - {f}" for f in found))
    lines += ["", "## Newly failing against the baseline", ""]
    old = {t["key"]: t for t in baseline[1]["turns"]}
    for name, r in runs:
        new = {t["key"]: t for t in r["turns"]}
        v1, v2 = newly_failing(old, new, "v1"), newly_failing(old, new, "v2")
        lines.append(f"- {name}: v1 {len(v1)}, v2 (both sides) {len(v2)}"
                     + "".join(f"\n  {x}" for x in v1 + v2))
    return lines


# Command line: write the comparison; never overwrite a report.
def main() -> None:
    out, base, runs = Path(sys.argv[1]), Path(sys.argv[2]), [Path(p) for p in sys.argv[3:]]
    if out.exists():
        sys.exit(f"{out} already exists; earlier reports are never rewritten.")
    lines = report((base.as_posix(), load(base)), [(p.stem, load(p)) for p in runs])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
