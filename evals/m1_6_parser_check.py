"""M1.6 check: score the Indian time and number parser on phrase sets.

Usage (one or more sets, each as "label=path"):
  python -m evals.m1_6_parser_check evals/reports/m1.6_parser_check_<date>.md \
      "phrase file=evals/scenarios/m1_6_indian_phrases.yaml"
Writes a new report; never overwrites an existing one.
"""

import sys
from datetime import datetime
from pathlib import Path

from evals.git_state import git_state
from evals.m1_6_scoring import AMBIGUOUS, FIELDS, accuracy, load_set, score_set
from evals.machine import machine_line

TARGET = 0.95
SECTIONS = {"t": "day words, clock, kal, midnight", "w": "weekdays", "r": "relative times",
            "o": "reminder offsets", "x": "not understood", "m": "numbers"}




# A case's report section: its `section` field, else the name for its id prefix.
def section_of(row: dict) -> str:
    return row["section"] or SECTIONS.get(row["id"][0], "other")


# Percentage text for (correct, total).
def pct(correct: int, total: int) -> str:
    return f"{correct}/{total} = {100 * correct / total:.1f} %" if total else "0/0"


# Only the fields that differ, as "field: want -> got".
def diff(row: dict) -> str:
    if row["kind"] == "number":
        return f"{row['want']} -> {row['got']}"
    return "; ".join(f"{f}: {row['want'][f]} -> {row['got'][f]}"
                     for f in FIELDS if row["want"][f] != row["got"][f])


# The short form of a time result for the ask table.
def brief(fields: dict) -> str:
    if fields["status"] == "ask":
        return f"ask ({fields['ask_about']})"
    if fields["status"] == "ok":
        return f"ok {fields['date']} {fields['time'] or ''}".strip()
    return fields["status"]


# The report section for one phrase set.
def set_section(label: str, path: str, rows: list[dict]) -> list[str]:
    correct, total = accuracy(rows)
    met = "MET" if total and correct / total >= TARGET else "NOT MET"
    lines = [f"## {label}", f"File: `{path}`", "",
             f"**Accuracy: {pct(correct, total)}** — target ≥ {TARGET:.0%}: **{met}**", "",
             "| section | correct |", "|---|---|"]
    for name in dict.fromkeys(section_of(r) for r in rows):
        part = [r for r in rows if section_of(r) == name]
        lines.append(f"| {name} | {pct(*accuracy(part))} |")
    failed = [r for r in rows if not r["ok"]]
    lines += ["", f"### Failures ({len(failed)})", ""]
    if failed:
        lines += ["| id | now | text | expected -> got | ambiguous words read as numbers |",
                  "|---|---|---|---|---|"]
        lines += [f"| {r['id']} | {r['now']} | {r['text']} | {diff(r)} | "
                  f"{', '.join(r['ambiguous_read']) or '-'} |" for r in failed]
    else:
        lines.append("None.")
    asks = [r for r in rows if r["kind"] == "time"
            and "ask" in (r["want"]["status"], r["got"]["status"])]
    lines += ["", f"### Ask cases ({len(asks)})",
              "Every case where ask was expected or returned.", "",
              "| id | now | text | expected | got | result |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['now']} | {r['text']} | {brief(r['want'])} | "
              f"{brief(r['got'])} | {'PASS' if r['ok'] else 'FAIL'} |" for r in asks]
    misread = [r["id"] for r in failed if r["ambiguous_read"]]
    lines += ["", "### Non-time words read as numbers",
              (f"Failures where an ambiguous word ({', '.join(sorted(AMBIGUOUS))}) "
              f"was read as a number: {', '.join(misread) if misread else 'none'}."), ""]
    return lines


# Score each "label=path" set and write the report.
def main() -> None:
    report = Path(sys.argv[1])
    if report.exists():
        sys.exit(f"{report} already exists; earlier reports are never rewritten.")
    lines = [f"# M1.6 parser check — {datetime.now():%Y-%m-%d %H:%M}", machine_line(),
             (f"Commit: {git_state()}. Parser: rules only (no LLM). "
             "A time case passes only when status, date, time, assumed_ampm, "
             "remind_before_min and ask_about all match."), ""]
    for spec in sys.argv[2:]:
        label, path = spec.split("=", 1)
        rows = score_set(load_set(Path(path)))
        lines += set_section(label, path, rows)
        print(f"{label}: {pct(*accuracy(rows))}")
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {report}")


if __name__ == "__main__":
    main()
