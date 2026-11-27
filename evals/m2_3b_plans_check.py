"""M2.3b plan-rule follow-up check: every message of evals/scenarios/m2_3b_plans_set.yaml
through Leo's real graph with memory on (mock tools, real LLM gateway, real
embedder) into a fresh temporary database, then the pass rule. For each
message the report says which rule of the write path keeps it out
(evals/m2_3b_plans_scoring.py) next to what the run actually stored.

Reported only, after the set: P10 (in the set), and R1 and P07 again after the
"Is" fix, read from the earlier M2.3b set files.

  python -m evals.m2_3b_plans_check <report stem>

Writes <stem>.md and <stem>.json; never overwrites a report or database.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

from evals import m2_3b_plans_scoring as ps
from evals.eval_paths import EVAL_DB_DIR
from evals.git_state import git_state
from evals.m2_3b_check_turns import mock_data, run_message
from evals.m2_3b_report import result_line
from evals.machine import machine_line
from leo.llm import gateway
from leo.llm.warmup import load_model
from leo.memory.memories import open_bank
from leo.memory.store import open_db
from leo.ml.embedder import load_embedder

SET_FILE = Path("evals/scenarios/m2_3b_plans_set.yaml")
EARLIER = {"R1": Path("evals/scenarios/m2_3b_fixround_set.yaml"),
           "P07": Path("evals/scenarios/m2_3b_memory_set.yaml")}


# The earlier set's message with this id (R1, P07).
def earlier_message(mid: str) -> dict:
    data = yaml.safe_load(EARLIER[mid].read_text(encoding="utf-8"))
    return next(m for g in data.values() if isinstance(g, list) for m in g if m["id"] == mid)


# Run one message and add the rule that keeps it out and the plan rule on its own.
def checked(message: dict, group: str, bank, config, now, mocks) -> dict:
    record = run_message(message, bank, config, now, mocks)
    print(f"{message['id']}: created {record['created']}", flush=True)
    return {**record, "group": group, "kept_out_by": ps.kept_out_by(message["text"], now),
            "plan_rule_alone": ps.plan_rule(message["text"], now)}


# One table row per message.
def rows(records: dict) -> list[str]:
    head = ("| id | group | message | stored (subject) | kept out by (code, write-path order) | "
            "plan rule alone | agents | turn s |")
    out = [head, "|---|---|---|---|---|---|---|---|"]
    for mid, r in records.items():
        out.append(f"| {mid} | {r['group']} | {r['text']} | {', '.join(r['subjects']) or 'no'} | "
                   f"{r['kept_out_by'] or '-'} | {r['plan_rule_alone'] or 'no'} | "
                   f"{', '.join(r['agents']) or '-'} | {r['turn_s']:.1f} |")
    return out


# The whole report.
def report(run: dict, config) -> list[str]:
    mismatch = [mid for mid, r in run["records"].items()
                if bool(r["created"]) == bool(r["kept_out_by"])]
    out = [f"# M2.3b plan-rule follow-up check ({datetime.now():%Y-%m-%d %H:%M})", "",
           run["machine"], f"Commit: {run['commit']}.", f"Check set: {SET_FILE.as_posix()}.",
           f"Now for every turn: {run['now']}. Local model: {config.llm.primary.model}.",
           f"Database left by the check: {run['db']}. All tools are mocks.", "",
           result_line(run["parts"]), "", "## Pass rule, part by part", ""]
    out += [f"- {'met' if ok else 'MISSED'}: {text}" for text, ok in run["parts"]]
    out += ["", "## Messages", "", ("\"Kept out by\" is the first rule of the write path "
            "that keeps the message out, read by code; \"stored\" is what the run wrote. "
            f"Messages where the two disagree: {mismatch or 'none'}."), ""]
    return out + rows(run["records"])


# Run the check and write the report files.
def main() -> None:
    stem = Path(sys.argv[1])
    md, js, db = stem.with_suffix(".md"), stem.with_suffix(".json"), EVAL_DB_DIR / f"{stem.name}.db"
    if any(p.exists() for p in (md, js, db)):
        sys.exit(f"{stem} report or database already exists; never rewritten.")
    EVAL_DB_DIR.mkdir(parents=True, exist_ok=True)
    config, data = gateway.load_config(), yaml.safe_load(SET_FILE.read_text(encoding="utf-8"))
    machine, commit, now = machine_line(), git_state(), datetime.fromisoformat(data["now"])
    embedder = load_embedder(config.embedder)
    load_model(config)
    bank = open_bank(open_db(db), embedder, config.memory, config.embedder.dimension)
    mocks, records = mock_data(), {}
    groups = [("plans", data["plans"]), ("facts", data["facts"]),
              ("reported only", data["reported_only"] + [earlier_message(i) for i in EARLIER])]
    for group, messages in groups:
        for m in messages:
            records[m["id"]] = checked(m, group, bank, config, now, mocks)
    run = {"machine": machine, "commit": commit, "now": data["now"], "db": db.as_posix(),
           "records": records, "parts": ps.parts(data["pass_rule"], data, records)}
    js.write_text(json.dumps(run, indent=1, default=str, ensure_ascii=False) + "\n",
                  encoding="utf-8")
    md.write_text("\n".join(report(run, config)) + "\n", encoding="utf-8")
    print(f"Wrote {md} and {js}; database {db}")


if __name__ == "__main__":
    main()
