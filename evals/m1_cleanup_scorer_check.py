"""M1 cleanup item 1: score the reply language scorers v1 and v2 on the
labelled check set evals/scenarios/m1_cleanup_language_replies.yaml.

  python -m evals.m1_cleanup_scorer_check evals/reports/m1_cleanup_scorer_check_<date>.md

v1 (evals/m1_8_scoring.py language_ok) only answers "is this reply in the
expected language?" for en and hinglish, and rejects every Devanagari reply,
so it has no result for "hi" cases ("n/a"). v2 names the language; it is
right when that equals the label. No LLM, no tools. Writes a new report and
never overwrites an existing one.
"""

import sys
from datetime import datetime
from pathlib import Path

import yaml

from evals.language_scoring_v2 import reply_language
from evals.m1_6_parser_check import git_state
from evals.m1_8_scoring import language_ok
from evals.machine import machine_line

CHECK_SET = Path("evals/scenarios/m1_cleanup_language_replies.yaml")
LABELS = ("en", "hinglish", "hi")


# Score one case: v1 verdict ("ok", "FAIL" or "n/a") and v2's language.
def score_case(case: dict) -> dict:
    reply, label, data = case["reply"], case["label"], case.get("tool_data", "")
    v1 = "n/a" if label == "hi" else ("ok" if language_ok(reply, label, data)[0] else "FAIL")
    v2, markers = reply_language(reply, data)
    return {**case, "v1": v1, "v2": v2, "v2_ok": v2 == label, "markers": markers}


# "a/b (p %)" for a list of booleans.
def rate(values: list[bool]) -> str:
    return f"{sum(values)}/{len(values)} ({100 * sum(values) / len(values):.1f} %)" if values else "-"


# The report lines.
def report(rows: list[dict], version: int) -> list[str]:
    lines = [f"# M1 cleanup scorer check — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             machine_line(), f"Commit: {git_state()}.",
             (f"Check set: {CHECK_SET.as_posix()} (version {version}), {len(rows)} replies. "
              "No LLM, no tools."), "",
             ("v1: evals/m1_8_scoring.py language_ok (no 'hi' class: n/a). "
              "v2: evals/language_scoring_v2.py reply_language, right when equal to the label."),
             "",
             "## Summary", "", "| label | cases | v1 right | v2 right |", "|---|---|---|---|"]
    for label in (*LABELS, "all"):
        group = [r for r in rows if label in ("all", r["label"])]
        v1 = [r["v1"] == "ok" for r in group if r["v1"] != "n/a"]
        lines.append(f"| {label} | {len(group)} | {rate(v1)} | {rate([r['v2_ok'] for r in group])} |")
    wrong = [r for r in rows if not r["v2_ok"] or r["v1"] == "FAIL"]
    lines += ["", f"## Cases where v1 or v2 is wrong ({len(wrong)})", ""]
    lines += [f"- {r['id']} ({r['label']}): v1 {r['v1']}, v2 {r['v2']} "
              f"(markers {r['markers']}): {r['reply']}" for r in wrong] or ["- none"]
    lines += ["", "## All cases", "", "| id | label | v1 | v2 | v2 markers | reply |",
              "|---|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['label']} | {r['v1']} | {r['v2']}{'' if r['v2_ok'] else ' (wrong)'} "
              f"| {', '.join(r['markers'])} | {r['reply'].replace('|', '/')} |" for r in rows]
    return lines


# Score the check set and write a new report.
def main() -> None:
    out = Path(sys.argv[1])
    if out.exists():
        sys.exit(f"{out} already exists; earlier reports are never rewritten.")
    data = yaml.safe_load(CHECK_SET.read_text(encoding="utf-8"))
    rows = [score_case(c) for c in data["cases"]]
    out.write_text("\n".join(report(rows, data["version"])) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
