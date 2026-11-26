"""M2.3 real check: long-term memory on the frozen check set. Writes a report.

  python -m evals.m2_3_memory_check REPORT_STEM [--part-a-only]
  (writes evals/reports/REPORT_STEM.md and REPORT_STEM.json)

Both question sets are scored: the original one and the fix round's fresh set
(evals/scenarios/m2_3_fix_questions.yaml). --part-a-only runs part A alone (no
LLM): used to measure the no-memory similarities for the fix-round threshold.

Runs, on this machine: part A (the pass rule, no LLM), the prompt-token cost
of the hints, part B (the real write path with the local model), and the
timing of the memory nodes (evals/m2_3_check_parts.py). Every database is a
temporary file, never leo_data/. Uses no personal data and no tools.
"""

import json
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from evals import m2_3_check_helpers as h
from evals.git_state import git_state
from evals.m2_3_check_parts import part_a, part_b, summarise_b, token_cost
from evals.machine import machine_line
from leo.config import load_config
from leo.language.memory_words import worth_remembering
from leo.llm.warmup import warm_up
from leo.memory.memories import open_bank
from leo.memory.store import open_db
from leo.ml.embedder import load_embedder

ROOT = Path(__file__).resolve().parent.parent
SET = ROOT / "evals" / "scenarios" / "m2_3_memory_questions.yaml"
FIX = ROOT / "evals" / "scenarios" / "m2_3_fix_questions.yaml"
REPORTS = ROOT / "evals" / "reports"


# Run `fn(bank)` on a memory bank in a fresh temporary database, closed afterwards.
def with_temp_bank(embedder, config, fn):
    with tempfile.TemporaryDirectory() as folder:
        conn = open_db(Path(folder) / "leo.db")
        try:
            return fn(open_bank(conn, embedder, config.memory, config.embedder.dimension))
        finally:
            conn.close()


# Recall@5 of each question set, and whether it reaches the fix set's minimum.
def set_results(a: dict, fix: dict) -> dict:
    rule = fix["rerun_rule"]
    return {name: {"recall5": h.recall_at(s["questions"], 5),
                   "reached": h.recall_at(s["questions"], 5) >= rule["min"]}
            for name, s in a["sets"].items()}


# Run every part (or part A only) and return the results as one dict.
def measure(part_a_only: bool = False) -> dict:
    config, data, fix = load_config(), h.load_yaml(SET), h.load_yaml(FIX)
    start = time.perf_counter()
    embedder = load_embedder(config.embedder)
    load_s = time.perf_counter() - start
    a, recall_times = with_temp_bank(embedder, config, lambda bank: part_a(bank, data, fix))
    head = {"config": config.memory.model_dump(), "embedder_load_s": load_s, "part_a": a,
            "passed": h.passed(a["sets"]["original"]["questions"], data["pass_rule"]),
            "sets": set_results(a, fix)}
    if part_a_only:
        return head
    warm_s = warm_up(config)
    tokens = token_cost(a["sets"]["original"]["questions"])

    # Part B and its summary on one fresh bank.
    def run_b(bank):
        rows, calls = part_b(bank, data)
        return rows, summarise_b(bank, data, rows, calls, fix)

    b_rows, b_summary = with_temp_bank(embedder, config, run_b)
    suite = h.suite_texts(ROOT / "evals" / "scenarios")
    picked = [t for t in suite if worth_remembering(t)]
    timing = {"recall_ms_part_a": h.spread(recall_times),
              "recall_ms_part_b": h.spread([r["recall_ms"] for r in b_rows]),
              "write_ms_not_picked": h.spread([r["write_ms"] for r in b_rows if not r["triggered"]]),
              "write_ms_picked": h.spread([r["write_ms"] for r in b_rows if r["triggered"]]),
              "extraction_s": b_summary.pop("extraction_s"),
              "suite_messages": len(suite), "suite_picked": picked}
    return {**head, "warm_up_s": warm_s, "tokens": tokens,
            "part_b": {"messages": b_rows, "summary": b_summary}, "timing": timing}


# The token and timing sections of the report.
def cost_lines(r: dict) -> list[str]:
    added = [t["added"] for t in r["tokens"] if t["hints"]]
    t = r["timing"]
    rate = len(t["suite_picked"]) / t["suite_messages"]
    lines = ["## Prompt tokens added by recall (responder prompt, with minus without hints)", "",
             "| Q | hints | without | with | added | providers |", "|---|---|---|---|---|---|"]
    lines += [f"| {x['id']} | {x['hints']} | {x.get('without', '-')} | {x.get('with', '-')} | "
              f"{x['added']} | {', '.join(x.get('providers', [])) or '-'} |" for x in r["tokens"]]
    lines += ["", (f"Questions with hints: {len(added)}/{len(r['tokens'])}; tokens added when "
              f"hints are given: {h.fmt(h.spread(added), 0)}."), "",
              "## Time", "",
              (f"- Embedder load: {r['embedder_load_s']:.1f} s; model warm-up: "
              f"{r['warm_up_s'] if r['warm_up_s'] is None else round(r['warm_up_s'], 2)} s."),
              (f"- memory_recall node (embed + search), part A questions: "
              f"{h.fmt(t['recall_ms_part_a'])} ms; part B messages: {h.fmt(t['recall_ms_part_b'])} ms."),
              (f"- memory_write node, message not picked by the word rule: "
              f"{h.fmt(t['write_ms_not_picked'], 2)} ms."),
              (f"- memory_write node, picked (one extraction call): {h.fmt(t['write_ms_picked'], 0)} ms;"
              f" extraction call alone: {h.fmt(t['extraction_s'], 2)} s."),
              (f"- Word rule on the {t['suite_messages']} M1.10 suite messages: "
              f"{len(t['suite_picked'])} picked ({rate:.0%}): {t['suite_picked']}.")]
    return lines


# Run the check and write REPORT_STEM.md and REPORT_STEM.json.
def main() -> None:
    stem = sys.argv[1]
    r = measure(part_a_only="--part-a-only" in sys.argv[2:])
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{stem}.json").write_text(json.dumps(r, indent=2, ensure_ascii=False, default=str),
                                          encoding="utf-8")
    verdict = "PASSED" if r["passed"] else "FAILED"
    lines = [f"# M2.3 memory check ({datetime.now():%Y-%m-%d %H:%M})", "", machine_line(),
             f"Commit: {git_state()}.", f"Check set: {SET.relative_to(ROOT).as_posix()}.",
             f"Memory settings: {r['config']}.", "",
             f"**Result: {verdict}** (part A Recall@5 >= 0.90 on the original 20 questions).",
             "Fix-round rerun rule, Recall@5 >= 0.90: " + "; ".join(
                 f"{name} {s['recall5']:.2f} ({'reached' if s['reached'] else 'below'})"
                 for name, s in r["sets"].items()) + ".", "",
             *h.part_a_lines(r["part_a"])]
    if "part_b" in r:
        lines += ["", *cost_lines(r), "", *h.part_b_lines(r["part_b"])]
    else:
        lines += ["", "Part A only (--part-a-only): no LLM call, no tokens, no part B."]
    (REPORTS / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{verdict}; wrote {stem}.md and {stem}.json")


if __name__ == "__main__":
    main()
