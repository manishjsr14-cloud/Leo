"""M1.10 eval suite: one command that runs every turn of the scenario files
listed in evals/scenarios/m1_10_suite.yaml through the real graph and the real
LLM gateway on MOCK tools, scores each turn, and writes one new report as
<stem>.md and <stem>.json (the .json is what eval_compare reads).

  python -m evals.run_eval <report stem> <label> [<baseline .json>]

e.g. python -m evals.run_eval evals/reports/m1.10_eval_2026-11-23_run1 run1
With a baseline, the report ends with the before/after comparison.
Earlier reports are never overwritten. Nothing touches a real calendar.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

from evals.eval_compare import compare
from evals.eval_metrics import compute
from evals.eval_report import body, sampling_line
from evals.eval_scoring import score, verdict
from evals.m1_7_calendar_check import git_state
from evals.m1_8_check import run_one
from evals.machine import machine_line
from leo.config import load_config

SUITE_FILE = Path("evals/scenarios/m1_10_suite.yaml")


# Read a YAML file.
def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# Every turn key ("file stem:id") that is known failing: marked so, or named in same_as.
def known_keys(files: list[tuple[Path, dict]]) -> dict[str, str]:
    known = {}
    for path, data in files:
        for turn in data["turns"]:
            if turn.get("known_failing"):
                known[f"{path.stem}:{turn['id']}"] = str(turn["from"])
                for key in turn.get("same_as", []):
                    known[key] = str(turn["from"])
    return known


# Run one turn: the turn with its language, and the file data with its calendar.
def run_turn(turn: dict, data: dict, lang: str, config) -> dict:
    turn = {**turn, "lang": turn.get("lang", lang)}
    data = dict(data)
    if "calendars" in data:
        data["mock_calendar"] = data["calendars"][turn["calendar"]]
    return run_one(turn, data, config, datetime.fromisoformat(data["now"]))


# The JSON-ready record of one scored turn.
def record(key: str, result: dict, known: dict[str, str]) -> dict:
    turn, calls = result["turn"], result["calls"]
    scored = score(result)
    return {"key": key, "lang": turn["lang"], "text": turn["text"], "reply": result["reply"],
            "plan": result["plan"], "stops": result["stops"], "steps": result["steps"],
            "calls": calls, "llm_calls": len(calls), "turn_s": result["wall"],
            "fallback_calls": sum(c["provider"] != "ollama" for c in calls),
            "from": known.get(key), "known": key in known,
            "verdict": verdict(scored["passed"], key in known), **scored}


# Header lines: title, machine, commit, models, sampling, files run and skipped.
def header(label: str, machine: str, commit: str, config, suite: dict,
           files: list[tuple[Path, dict]]) -> list[str]:
    runs = ", ".join(f"{p.as_posix()} (version {d['version']}, now {d['now']})" for p, d in files)
    skips = [f"- skipped {s['file']}: {s['why']}" for s in suite["skip"]]
    return [f"# M1.10 eval ({label}) — {datetime.now().strftime('%Y-%m-%d %H:%M')}", machine,
            f"Commit: {commit}.",
            (f"Local model: {config.llm.primary.model}. Fallback: {config.llm.fallback.model}. "
             f"agent.max_steps: {config.agent.max_steps}. All tools are mocks."),
            sampling_line(config), "",
            f"Suite: {SUITE_FILE.as_posix()} (version {suite['version']}). Files run: {runs}.",
            *skips, ""]


# Run the suite and write the new report files.
def main() -> None:
    stem, label = Path(sys.argv[1]), sys.argv[2]
    # Not with_suffix: "m1.10_eval_..." would lose everything after "m1".
    md, js = stem.parent / f"{stem.name}.md", stem.parent / f"{stem.name}.json"
    if md.exists() or js.exists():
        sys.exit(f"{stem}.md/.json already exists; earlier reports are never rewritten.")
    baseline = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    config, suite = load_config(), load(SUITE_FILE)
    machine, commit = machine_line(), git_state()
    files = [(Path(entry["file"]), load(Path(entry["file"]))) for entry in suite["run"]]
    known = known_keys(files)
    records = []
    for entry, (path, data) in zip(suite["run"], files):
        for turn in data["turns"]:
            lang = entry.get("lang", {}).get(turn["id"])
            key = f"{path.stem}:{turn['id']}"
            records.append(record(key, run_turn(turn, data, lang, config), known))
            print(f"{key}: {records[-1]['verdict']}", flush=True)
    report = {"label": label, "machine": machine, "commit": commit.split()[0],
              "dirty": "uncommitted" in commit, "model": config.llm.primary.model,
              "sampling": sampling_line(config), "metrics": compute(records), "turns": records}
    comparison = []
    if baseline:
        before = json.loads(baseline.read_text(encoding="utf-8"))
        comparison = compare(before, report, baseline.as_posix(), js.as_posix())
    lines = header(label, machine, commit, config, suite, files)
    lines += body(records, report["metrics"], comparison)
    js.write_text(json.dumps(report, indent=1, default=str, ensure_ascii=False) + "\n",
                  encoding="utf-8")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Wrote {md} and {js}")


if __name__ == "__main__":
    main()
