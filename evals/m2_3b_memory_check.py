"""M2.3b memory check: every message of evals/scenarios/m2_3b_memory_set.yaml, in
the set's order, through Leo's real graph with memory on (mock tools, real LLM
gateway, real embedder), into a fresh database; then the done rule. Since the
fix round, the fix-round set (m2_3b_fixround_set.yaml) runs next in the same
store and gets its own report, <stem>_fixround.md; it decides the result.

  python -m evals.m2_3b_memory_check <report stem>

Writes <stem>.md and <stem>.json and keeps the database the check left at
<temp>/leo_evals/<stem name>.db (evals/eval_paths.py, never leo_data/), for the M1.10 regression run with
memory (evals/run_eval.py --memory-db). The five small-talk messages the user
asked for at approval (reported only, not in the frozen set) run afterwards on
a COPY of that database, so they do not change it. Earlier reports and
databases are never overwritten.
"""

import json
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from evals import m2_3b_report as report
from evals import m2_3b_report_fix as report_fix
from evals import m2_3b_scoring as s
from evals.eval_paths import EVAL_DB_DIR
from evals.git_state import git_state
from evals.m2_3b_check_turns import memory_rows, mock_data, run_message
from evals.machine import machine_line
from leo.language.memory_words import is_personal_question
from leo.llm import gateway
from leo.llm.warmup import load_model
from leo.memory.memories import open_bank, search_memories
from leo.memory.store import open_db
from leo.ml.embedder import load_embedder

SET_FILE = Path("evals/scenarios/m2_3b_memory_set.yaml")
FIX_FILE = Path("evals/scenarios/m2_3b_fixround_set.yaml")
DB_DIR = EVAL_DB_DIR
ORDER = ("facts", "plans", "same_topic_no_cue", "updates", "boundary", "questions",
         "unanswerable")
FIX_ORDER = ("plans", "small_talk", "same_topic_no_cue", "updates", "reported_only",
             "questions", "unanswerable")
SMALL_TALK = ["Main theek hoon", "I agree", "I'm fine, thanks", "I think so",
              "Haan main aa raha hoon"]


# Open a memory bank on a database file with the loaded embedder.
def bank_on(path: Path, embedder, config):
    return open_bank(open_db(path), embedder, config.memory, config.embedder.dimension)


# The gate and the 5 nearest active memory rows for a question, before its turn.
def search_before(bank, text: str) -> tuple[bool, list[int]]:
    found = search_memories(bank, bank.embedder.embed_query(text), 5)
    return is_personal_question(text), [m.id for m in found]


# Run the small-talk messages on a copy of the check's database.
def small_talk(bank, copy: Path, embedder, config, now, data) -> list[dict]:
    target = sqlite3.connect(copy)
    bank.conn.backup(target)
    target.close()
    other = bank_on(copy, embedder, config)
    return [run_message({"id": f"S{i}", "text": t}, other, config, now, data)
            for i, t in enumerate(SMALL_TALK, 1)]


# Run every message of one set, in order, into the bank. Returns (records by
# id, gate and top-5 rows for each question, searched before its turn).
def run_set(data: dict, order: tuple, prefix: str, bank, config, now, mocks):
    records, searches = {}, {}
    for group in order:
        for message in data[group]:
            if group in ("questions", "unanswerable"):
                searches[message["id"]] = search_before(bank, message["text"])
            records[message["id"]] = {**run_message(message, bank, config, now, mocks),
                                      "group": prefix + group}
            print(f"{message['id']}: created {records[message['id']]['created']}", flush=True)
    return records, searches


# Question results and unanswerable replies for one set.
def answers(data: dict, records: dict, searches: dict, by_message: dict):
    questions = [s.question_result(q, *searches[q["id"]], by_message) for q in data["questions"]]
    unanswerable = [{"id": x["id"], "text": x["text"], "reply": records[x["id"]]["reply"],
                     "gate": searches[x["id"]][0],
                     "dont_know": s.says_dont_know(records[x["id"]]["reply"])}
                    for x in data["unanswerable"]]
    return questions, unanswerable


# Run the check and write the report files.
def main() -> None:
    stem = Path(sys.argv[1])
    md, js = stem.parent / f"{stem.name}.md", stem.parent / f"{stem.name}.json"
    fix_md = stem.parent / f"{stem.name}_fixround.md"
    db, copy = DB_DIR / f"{stem.name}.db", DB_DIR / f"{stem.name}_small_talk.db"
    if any(p.exists() for p in (md, js, fix_md, db, copy)):
        sys.exit(f"{stem} report or database already exists; never rewritten.")
    DB_DIR.mkdir(parents=True, exist_ok=True)
    config, data = gateway.load_config(), yaml.safe_load(SET_FILE.read_text(encoding="utf-8"))
    fix = yaml.safe_load(FIX_FILE.read_text(encoding="utf-8"))
    machine, commit, now = machine_line(), git_state(), datetime.fromisoformat(data["now"])
    start = time.perf_counter()
    embedder = load_embedder(config.embedder)
    load_s = time.perf_counter() - start
    warm_s = load_model(config)
    bank, mocks = bank_on(db, embedder, config), mock_data()
    records, searches = run_set(data, ORDER, "", bank, config, now, mocks)
    fix_records, fix_searches = run_set(fix, FIX_ORDER, "fix_", bank, config, now, mocks)
    all_records = {**records, **fix_records}
    rows, by_message = memory_rows(bank), s.rows_by_message(all_records)
    talk = small_talk(bank, copy, embedder, config, now, mocks)
    questions, unanswerable = answers(data, records, searches, by_message)
    fix_q, fix_x = answers(fix, fix_records, fix_searches, by_message)
    base = {"machine": machine, "commit": commit, "db": db.as_posix(), "rows": rows,
            "embedder_load_s": load_s, "warm_up_s": warm_s, "small_talk": talk}
    run = {**base, "records": records, "questions": questions, "unanswerable": unanswerable,
           "parts": s.done_parts(data["done_rule"], data, all_records, rows, questions,
                                 unanswerable)}
    fix_run = {**base, "records": fix_records, "questions": fix_q, "unanswerable": fix_x,
               "parts": s.fix_parts(fix["pass_rule"], fix, all_records, rows, fix_q, fix_x)}
    js.write_text(json.dumps({"original": run, "fixround": fix_run}, indent=1, default=str,
                             ensure_ascii=False) + "\n", encoding="utf-8")
    md.write_text("\n".join(report.lines(run, data, config)) + "\n", encoding="utf-8")
    fix_md.write_text("\n".join(report_fix.lines(fix_run, fix, config)) + "\n",
                      encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Wrote {md}, {fix_md} and {js}; database {db}")


if __name__ == "__main__":
    main()
