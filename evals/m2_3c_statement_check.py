"""M2.3c check: every message of evals/scenarios/m2_3c_statement_set.yaml through
Leo's real graph with memory on (MOCK tools, real LLM gateway, real embedder,
a fresh temporary database), then the pass rule (evals/m2_3c_scoring.py).

Every count comes from the mock tools' log of each turn (each tool call that
actually ran). The report lists, per message, the kind read by code
(leo/language/turn_kind.py), the agents that ran, the tool log and the reply.
The M1.10 part of the pass rule is judged from the M1.10 regression report,
and the t09 reply is the user's judgement; this report does not judge them.

  python -m evals.m2_3c_statement_check <report stem> [--set fixround]

--set fixround runs the fix-round set (evals/scenarios/m2_3c_fixround_set.yaml,
scored by evals/m2_3c_fix_scoring.py); its report says the set is not blind.

Writes <stem>.md and <stem>.json; never overwrites a report or database.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

from evals import m2_3c_scoring as sc
from evals.eval_paths import EVAL_DB_DIR
from evals.git_state import git_state
from evals.m2_3b_check_turns import mock_data, run_message
from evals.m2_3c_fix_scoring import fix_parts
from evals.machine import machine_line
from leo.language.turn_kind import turn_kind
from leo.llm import gateway
from leo.llm.warmup import load_model
from leo.memory.memories import open_bank
from leo.memory.store import open_db
from leo.ml.embedder import load_embedder

ELSEWHERE = [("- judged elsewhere: the M1.10 suite, no new failures against "
             "evals/reports/m1.10_eval_2026-11-23_run1.json, t09 excluded")]
# set name -> (file, groups in run order, lines added after the parts)
SETS = {
    "first": (Path("evals/scenarios/m2_3c_statement_set.yaml"),
              ["statements", "questions", "requests", "behaviour_change", "reported_only"],
              [*ELSEWHERE, ("- user's judgement: the t09 reply offers to add it (or asks), "
               "without claiming it was added")]),
    "fixround": (Path("evals/scenarios/m2_3c_fixround_set.yaml"),
                 ["event_statements", "first_person_statements", "requests"],
                 [*ELSEWHERE, ("- NOT blind: this set was written by Claude after the "
                  "fix-round design (fixes a and b)")]),
}


# The result line from the parts this report judges.
def result_line(parts: list) -> str:
    if all(ok for _, ok in parts):
        return ("**Result of this check's parts: met** (the M1.10 part is judged from its "
                "own report).")
    return "**Result: NOT MET** (at least one part of the pass rule missed)."


# One tool log as text: "tool(args) -> result; ..." or "none".
def log_text(log: list[dict]) -> str:
    return "; ".join(f"`{c['tool']}({c['args']})` -> `{c['result']}`" for c in log) or "none"


# One section per message: kind, agents, tool log, reply.
def details(records: dict) -> list[str]:
    out = []
    for mid, r in records.items():
        out += [f"### {mid} ({r['group']}): {r['text']}", "",
                (f"- kind (code): {r['kind']}; agents: {', '.join(r['agents']) or 'none'}; "
                f"LLM calls: {len(r['calls'])}; turn {r['turn_s']:.1f} s"),
                f"- mock tools' log: {log_text(r['tool_log'])}",
                f"- memory rows created: {r['created'] or 'none'}",
                f"- reply: {r['reply']}"]
        out += [f"- note: {r['note']}"] if r.get("note") else []
        out.append("")
    return out


# The whole report.
def report(run: dict, config) -> list[str]:
    out = [f"# M2.3c statement check ({datetime.now():%Y-%m-%d %H:%M})", "",
           run["machine"], f"Commit: {run['commit']}.",
           f"Check set: {SETS[run['set']][0].as_posix()}.",
           f"Now for every turn: {run['now']}. Local model: {config.llm.primary.model}.",
           f"Database left by the check: {run['db']}. All tools are mocks.", "",
           result_line(run["parts"]), "", "## Pass rule, part by part", ""]
    out += [f"- {'met' if ok else 'MISSED'}: {text}" for text, ok in run["parts"]]
    out += [*SETS[run["set"]][2], "",
            "| id | group | kind (code) | agents | tool calls | write calls |",
            "|---|---|---|---|---|---|"]
    out += [f"| {mid} | {r['group']} | {r['kind']} | {', '.join(r['agents']) or '-'} | "
            f"{', '.join(c['tool'] for c in r['tool_log']) or '-'} | "
            f"{', '.join(c['tool'] for c in sc.write_calls(r['tool_log'])) or '-'} |"
            for mid, r in run["records"].items()]
    return out + ["", "## Messages", ""] + details(run["records"])


# Run the check and write the report files.
def main() -> None:
    stem, name = Path(sys.argv[1]), "fixround" if sys.argv[2:] == ["--set", "fixround"] else "first"
    set_file, groups, _ = SETS[name]
    md, js = stem.parent / f"{stem.name}.md", stem.parent / f"{stem.name}.json"
    db = EVAL_DB_DIR / f"{stem.name}.db"
    if any(p.exists() for p in (md, js, db)):
        sys.exit(f"{stem} report or database already exists; never rewritten.")
    EVAL_DB_DIR.mkdir(parents=True, exist_ok=True)
    config, data = gateway.load_config(), yaml.safe_load(set_file.read_text(encoding="utf-8"))
    machine, commit, now = machine_line(), git_state(), datetime.fromisoformat(data["now"])
    embedder = load_embedder(config.embedder)
    load_model(config)
    bank = open_bank(open_db(db), embedder, config.memory, config.embedder.dimension)
    mocks, records = mock_data(), {}
    for group in groups:
        for m in data[group]:
            record = run_message(m, bank, config, now, mocks)
            records[m["id"]] = {**record, "group": group, "kind": turn_kind(m["text"]),
                                "note": m.get("note")}
            print(f"{m['id']}: {[c['tool'] for c in record['tool_log']]}", flush=True)
    parts = fix_parts(data, records, now) if name == "fixround" else sc.parts(data, records)
    run = {"set": name, "machine": machine, "commit": commit, "now": data["now"],
           "db": db.as_posix(), "records": records, "parts": parts}
    js.write_text(json.dumps(run, indent=1, default=str, ensure_ascii=False) + "\n",
                  encoding="utf-8")
    md.write_text("\n".join(report(run, config)) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Wrote {md} and {js}; database {db}")


if __name__ == "__main__":
    main()
