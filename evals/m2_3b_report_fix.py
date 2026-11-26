"""The Markdown report for the M2.3b fix-round set (run by evals/m2_3b_memory_check.py
right after the original set, in the same store). This set decides the fix-round result."""

from datetime import datetime

from evals import m2_3b_scoring as s
from evals.m2_3b_report import message_rows, result_line, time_lines
from leo.language.memory_events import is_plan_or_event
from leo.language.memory_words import is_question


# The whole fix-round report.
def lines(run: dict, data: dict, config) -> list[str]:
    now, records = datetime.fromisoformat(data["now"]), run["records"]
    out = [f"# M2.3b fix-round check ({datetime.now():%Y-%m-%d %H:%M})", "", run["machine"],
           f"Commit: {run['commit']}.",
           ("Check set: evals/scenarios/m2_3b_fixround_set.yaml (run right after "
            "evals/scenarios/m2_3b_memory_set.yaml, in the same store; this set decides the "
            "fix-round result)."),
           f"Local model: {config.llm.primary.model}. Memory settings: {config.memory.model_dump()}.",
           f"Database left by the check: {run['db']}. All tools are mocks.", "",
           result_line(run["parts"]), "", "## Pass rule, part by part", ""]
    out += [f"- {'met' if ok else ('the user judges' if ok is None else 'MISSED')}: {text}"
            for text, ok in run["parts"]]
    out += ["", ("Not blind: the small-talk rule (rule A) was written after reading S01-S06, "
                 "so the small-talk part is not an independent result."),
            (f"Other replacements by fix-round messages: "
             f"{s.other_replacements(data, records) or 'none'}."), "", "## Messages", ""]
    out += message_rows(run)
    lang = {q["id"]: (q["lang"], q["text"]) for q in data["questions"]}
    out += ["", "## Questions (Recall@5; hit3 = among the 3 hints given)", "",
            "| id | lang | question | gate | rank in top 5 | hit5 | hit3 |",
            "|---|---|---|---|---|---|---|"]
    out += [f"| {q['id']} | {lang[q['id']][0]} | {lang[q['id']][1]} | {q['gate']} | "
            f"{q['rank'] or 'missed'} | {q['hit5']} | {q['hit3']} |" for q in run["questions"]]
    out += ["", (f"Recall@3 (in the hints): {sum(q['hit3'] for q in run['questions'])}/"
                 f"{len(run['questions'])}."), "", "## Unanswerable questions: replies in full", ""]
    out += [f"- {x['id']} (gate {x['gate']}, don't-know phrase: {x['dont_know']}): {x['text']}\n"
            f"  > {x['reply']}" for x in run["unanswerable"]]
    r1 = data["reported_only"][0]
    out += ["", "## Reported only", "",
            (f"- R1 ({r1['text']}): read as a question: {is_question(r1['text'])}; plan rule: "
             f"{is_plan_or_event(r1['text'], now)}; stored: {records['R1']['subjects'] or 'no'}."),
            "", "## Time (fix-round set)", ""]
    return out + time_lines(run)
