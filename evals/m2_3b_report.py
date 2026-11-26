"""The Markdown report of the M2.3b memory check (run by evals/m2_3b_memory_check.py)."""

from datetime import datetime
from pathlib import Path
from statistics import median

import yaml

from evals import m2_3b_scoring as s
from leo.language.memory_events import is_plan_or_event
from leo.language.memory_words import (
    is_personal_question,
    is_question,
    worth_remembering,
)

SUITE = Path("evals/scenarios/m1_10_suite.yaml")


# "median x (min a, max b, n c)" for a list of numbers.
def spread(values: list[float], digits: int = 2) -> str:
    if not values:
        return "none"
    return (f"median {median(values):.{digits}f} (min {min(values):.{digits}f}, "
            f"max {max(values):.{digits}f}, n {len(values)})")


# The overall result from the done-rule parts.
def result_line(parts: list) -> str:
    if any(ok is False for _, ok in parts):
        return "**Result: NOT MET** (at least one part of the done rule missed)."
    if any(ok is None for _, ok in parts):
        return "**Result: every counted part met; the unanswerable replies need the user's judgement.**"
    return "**Result: PASSED** (every part of the done rule met)."


# One table row per message: what its turn stored and replaced, and its calls.
def message_rows(run: dict) -> list[str]:
    out = ["| id | group | stored (subject) | replaced rows | agents | LLM calls | turn s |",
           "|---|---|---|---|---|---|---|"]
    for mid, r in run["records"].items():
        calls = ", ".join(f"{c['node']}:{c['provider']}" for c in r["calls"])
        out.append(f"| {mid} | {r['group']} | {', '.join(r['subjects']) or '-'} | "
                   f"{r['replaced'] or '-'} | {', '.join(r['agents']) or '-'} | {calls} | "
                   f"{r['turn_s']:.1f} |")
    return out


# The 42 M1.10 suite messages under the M2.3b word rules (code only, no LLM).
def suite_counts(now: datetime) -> list[str]:
    suite = yaml.safe_load(SUITE.read_text(encoding="utf-8"))
    texts = [t["text"] for e in suite["run"]
             for t in yaml.safe_load(Path(e["file"]).read_text(encoding="utf-8"))["turns"]]
    gate = [t for t in texts if is_personal_question(t)]
    write = [t for t in texts if worth_remembering(t) and not is_plan_or_event(t, now)]
    return [(f"- M1.10 suite messages ({len(texts)}), code rules only: gate opens for "
            f"{len(gate)}, a write would be triggered for {len(write)}."),
            *[f"  - gate: {t}" for t in gate], *[f"  - write: {t}" for t in write]]


# Times: loads, extraction calls, turns by group.
def time_lines(run: dict) -> list[str]:
    calls = [c for r in run["records"].values() for c in r["calls"]]
    memory = [c["total_s"] for c in calls if c["node"] == "memory"]
    providers = sorted({c["provider"] for c in calls})
    lines = [(f"- Embedder load: {run['embedder_load_s']:.1f} s; model warm-up: "
             f"{run['warm_up_s'] if run['warm_up_s'] is None else round(run['warm_up_s'], 2)} s."),
             f"- Memory extraction call: {spread(memory)} s.",
             (f"- LLM calls: {len(calls)}; providers: {providers}; fallback calls: "
             f"{sum(c['provider'] != 'ollama' for c in calls)}.")]
    groups = sorted({r["group"] for r in run["records"].values()})
    for g in groups:
        times = [r["turn_s"] for r in run["records"].values() if r["group"] == g]
        lines.append(f"- Turn time, {g}: {spread(times, 1)} s.")
    return lines


# The whole report.
def lines(run: dict, data: dict, config) -> list[str]:
    now, records = datetime.fromisoformat(data["now"]), run["records"]
    by_message, cued = s.rows_by_message(records), s.cued_updates(data, records, run["rows"])
    out = [f"# M2.3b memory check ({datetime.now():%Y-%m-%d %H:%M})", "", run["machine"],
           f"Commit: {run['commit']}.", "Check set: evals/scenarios/m2_3b_memory_set.yaml.",
           f"Local model: {config.llm.primary.model}. Memory settings: {config.memory.model_dump()}.",
           f"Database left by the check: {run['db']}. All tools are mocks.", "",
           result_line(run["parts"]), "", "## Done rule, part by part", ""]
    out += [f"- {'met' if ok else ('the user judges' if ok is None else 'MISSED')}: {text}"
            for text, ok in run["parts"]]
    out += ["", (f"Lasting facts not stored: {s.not_stored(data, records) or 'none'}. "
            f"Plans stored: {s.plans_stored(data, records) or 'none'}."),
            f"Cued updates: {cued}.", (f"Replacements by other messages: "
            f"{s.other_replacements(data, records) or 'none'}."), "", "## Messages", ""]
    out += message_rows(run)
    out += ["", "## Questions (Recall@5; hit3 = among the 3 hints given)", "",
            "| id | lang | gate | rank in top 5 | hit5 | hit3 |", "|---|---|---|---|---|---|"]
    lang = {q["id"]: q["lang"] for q in data["questions"]}
    out += [f"| {q['id']} | {lang[q['id']]} | {q['gate']} | {q['rank'] or 'missed'} | "
            f"{q['hit5']} | {q['hit3']} |" for q in run["questions"]]
    out += ["", (f"Recall@3 (in the hints): {sum(q['hit3'] for q in run['questions'])}/"
            f"{len(run['questions'])}."), "", "## Unanswerable questions: replies in full", ""]
    out += [f"- {x['id']} (gate {x['gate']}, don't-know phrase: {x['dont_know']}): {x['text']}\n"
            f"  > {x['reply']}" for x in run["unanswerable"]]
    out += ["", "## Boundary group (reported only)", ""]
    out += [f"- {b['id']}: {b['text']} -> stored: {records[b['id']]['subjects'] or 'no'}"
            for b in data["boundary"]]
    p07 = records["P07"]
    out += ["", (f"P07 ({p07['text']}): read as a question by the question rule: "
            f"{is_question(p07['text'])}; plan rule: {is_plan_or_event(p07['text'], now)}; "
            f"stored: {p07['subjects'] or 'no'}."), "", ("## Small talk (reported only, "
            "on a copy of the database)"), ""]
    out += [f"- {t['text']} -> stored: {t['subjects'] or 'no'}" for t in run["small_talk"]]
    out += ["", "## M1.10 suite under the word rules", "", *suite_counts(now), "", "## Time", ""]
    out += time_lines(run)
    out += ["", f"Message ids -> memory rows: {by_message}."]
    return out
