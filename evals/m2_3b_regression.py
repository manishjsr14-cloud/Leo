"""M2.3b regression check: the M1.10 suite with memory on shows no new failures.

  python -m evals.m2_3b_regression <report stem> <run.json> [<run.json> ...]

Each run is an evals/run_eval.py report made with --memory-db (an empty store,
or the store the M2.3b check left). Rule, agreed at approval: no newly failing
turn against the M1.10 laptop baseline, judged with scorer v2 on both sides
(the M1 cleanup done check's comparison); v1 alongside. Also reported: how many
suite messages open the recall gate and trigger a write (code rules), and how
many memory rows each run actually added. It only reads reports.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from evals.m1_cleanup_done_check import BASELINE, check, load
from leo.language.memory_events import is_plan_or_event
from leo.language.memory_words import is_personal_question, worth_remembering
from leo.language.normalize import normalize


# Gate and write counts for a run's turn texts (as normalized by the CLI).
def rule_counts(run: dict, now: datetime) -> tuple[list[str], list[str]]:
    texts = [normalize(t["text"]) for t in run["turns"]]
    gate = [t for t in texts if is_personal_question(t)]
    write = [t for t in texts if worth_remembering(t) and not is_plan_or_event(t, now)]
    return gate, write


# Report lines for one run, and whether it passed.
def run_lines(path: Path, baseline: dict) -> tuple[bool, list[str]]:
    run = load(path)
    passed, lines = check(run, baseline)
    memory = run.get("memory") or {}
    gate, write = rule_counts(run, datetime.now())
    added = (memory.get("rows_after") or 0) - (memory.get("rows_before") or 0)
    return passed, [f"## {path.as_posix()}", "", (f"- memory store: {memory.get('from')}; rows "
                    f"before {memory.get('rows_before')}, after {memory.get('rows_after')} "
                    f"(added {added})"), *lines,
                    f"- suite messages that open the recall gate: {len(gate)}/{len(run['turns'])}",
                    *[f"  - {t}" for t in gate],
                    f"- suite messages that trigger a write: {len(write)}/{len(run['turns'])}",
                    *[f"  - {t}" for t in write], ""]


# Check every run and write the report.
def main() -> None:
    stem, runs = Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]]
    md = stem.parent / f"{stem.name}.md"
    if md.exists():
        sys.exit(f"{md} already exists; earlier reports are never rewritten.")
    baseline = load(BASELINE)
    results = [run_lines(path, baseline) for path in runs]
    ok = all(passed for passed, _ in results) and bool(results)
    lines = [f"# M2.3b regression: M1.10 suite with memory on ({datetime.now():%Y-%m-%d %H:%M})",
             "", f"Baseline: {BASELINE.as_posix()} (M1.10 laptop baseline).", "",
             (f"**Result: {'PASSED' if ok else 'NOT MET'}** (no newly failing turn under scorer "
             "v2 in every run, on the laptop)."), ""]
    for _, part in results:
        lines += part
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"passed": ok, "report": md.as_posix()}))


if __name__ == "__main__":
    main()
