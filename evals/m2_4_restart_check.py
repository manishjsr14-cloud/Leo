"""M2.4 restart check: one long conversation, a hard kill, then facts referred back to.

  python -m evals.m2_4_restart_check <report stem>

For each variant ("summary", then "no_summary" for the token comparison) it
starts evals/m2_4_child.py on a fresh database in <temp>/leo_evals/ (never
leo_data/) for P01-P20. When that process says it is waiting for the next
message, it is hard-killed (Popen.kill: TerminateProcess on Windows, no clean
shutdown). A new process on the same database and thread prints the state it
finds and runs R5, R6, R1-R4. The pass rule (evals/m2_4_scoring.py, the user's
rule in the set) is judged on the "summary" variant; the "no_summary" variant
is reported only. Memory is off; all tools are mocks.

Writes <stem>.md and <stem>.json; never overwrites a report or database.
"""

import json
import subprocess
import sys
from pathlib import Path

import yaml

from evals import m2_4_scoring as sc
from evals.eval_paths import EVAL_DB_DIR
from evals.git_state import git_state
from evals.m2_4_child import SET
from evals.m2_4_report import report
from evals.machine import machine_line
from leo.llm import gateway

VARIANTS = ["summary", "no_summary"]


# Run one child process and collect its events. The child is hard-killed as
# soon as it says it is waiting for the next message (part 1 only says so).
def run_child(db: Path, variant: str, part: str) -> dict:
    command = [sys.executable, "-m", "evals.m2_4_child", str(db), variant, part]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            text=True, encoding="utf-8")
    events, killed = [], False
    for line in proc.stdout:
        event = json.loads(line)
        events.append(event)
        print(f"[{variant} part {part}] {event['event']} {event.get('id', '')}", flush=True)
        if event["event"] == "waiting":
            proc.kill()
            killed = True
            break
    code = proc.wait()
    return {"events": events, "killed": killed, "exit_code": code}


# One variant: part 1, the kill, part 2.
def run_variant(db: Path, variant: str, data: dict) -> dict:
    first, second = run_child(db, variant, "1"), run_child(db, variant, "2")
    return {"db": str(db), **assemble(first, second, data)}


# Both parts' events as one run: the turns keyed by id (after-restart turns with
# their expected keys), the state before the kill and the state found after it.
def assemble(first: dict, second: dict, data: dict) -> dict:
    keys = {t["id"]: t["expect_any_of"] for t in data["after_restart"]}
    turns = {e["id"]: e for e in first["events"] + second["events"] if e["event"] == "turn"}
    for tid, k in keys.items():
        if tid in turns:
            turns[tid]["keys"] = k
    state = {e["event"]: e["state"] for e in first["events"] if "state" in e}
    after = next((e["state"] for e in second["events"] if e["event"] == "start"), None)
    return {"turns": turns, "before_kill": state.get("state"),
            "after_restart": after, "part1_killed": first["killed"],
            "part1_exit_code": first["exit_code"], "part2_exit_code": second["exit_code"]}


# Judge the pass rule for one variant (None when a part did not finish).
def judge(run: dict, data: dict) -> list | None:
    rule, turns = data["pass_rule"], run["turns"]
    needed = rule["recent_answered"] + rule["summarized"]
    if run["before_kill"] is None or run["after_restart"] is None or \
            any(i not in turns for i in needed):
        return None
    return sc.pass_parts(rule, turns, run["before_kill"], run["after_restart"])


# Run the check and write the report files.
def main() -> None:
    stem = Path(sys.argv[1])
    md, js = stem.parent / f"{stem.name}.md", stem.parent / f"{stem.name}.json"
    dbs = {v: EVAL_DB_DIR / f"{stem.name}_{v}.db" for v in VARIANTS}
    if any(p.exists() for p in (md, js, *dbs.values())):
        sys.exit(f"{stem} report or database already exists; never rewritten.")
    EVAL_DB_DIR.mkdir(parents=True, exist_ok=True)
    config, data = gateway.load_config(), yaml.safe_load(SET.read_text(encoding="utf-8"))
    machine, commit = machine_line(), git_state()
    runs = {v: run_variant(dbs[v], v, data) for v in VARIANTS}
    for run in runs.values():
        run["parts"] = judge(run, data)
    result = {"machine": machine, "commit": commit, "set": SET.as_posix(), "now": data["now"],
              "model": config.llm.primary.model,
              "conversation": config.conversation.model_dump(), "runs": runs}
    js.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    md.write_text("\n".join(report(result, data)) + "\n", encoding="utf-8")
    print(f"Wrote {md} and {js}")


if __name__ == "__main__":
    main()
