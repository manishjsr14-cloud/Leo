"""Scoring and report lines for the M2.3 memory check (no model needed here).

The check set is evals/scenarios/m2_3_memory_questions.yaml. A question is a hit
when its expected fact's text is among the search results (top 5, no threshold).
Pass rule (part A, fixed in that file): Recall@5 >= 0.90 over the 20 questions.
"""

import statistics
from pathlib import Path

import yaml

SUITE_FILES = ["m1_7_calendar_turns.yaml", "m1_8_language_turns.yaml",
               "m1_10_known_failing.yaml"]


# Read a YAML file.
def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# The 1-based rank of `expected` among the result texts, or None when absent.
def rank_of(expected: str, texts: list[str]) -> int | None:
    return texts.index(expected) + 1 if expected in texts else None


# Recall@k over rows that each have a "rank" (None = not found).
def recall_at(rows: list[dict], k: int) -> float:
    hits = sum(1 for r in rows if r["rank"] is not None and r["rank"] <= k)
    return hits / len(rows) if rows else 0.0


# Did the rule pass? Recall@5 at or above the file's minimum, on the right count.
def passed(rows: list[dict], rule: dict) -> bool:
    return len(rows) == rule["questions"] and recall_at(rows, 5) >= rule["min"]


# Every message text of the M1.10 suite's turn files (for the trigger rate).
def suite_texts(scenarios: Path) -> list[str]:
    return [t["text"] for name in SUITE_FILES for t in load_yaml(scenarios / name)["turns"]]


# Median, min and max of a list of numbers, or None when empty.
def spread(values: list[float]) -> dict | None:
    if not values:
        return None
    return {"n": len(values), "median": statistics.median(values),
            "min": min(values), "max": max(values)}


# "median 12.3 (min 10.1, max 40.2, n 20)" or "-".
def fmt(s: dict | None, digits: int = 1) -> str:
    if s is None:
        return "-"
    return (f"median {s['median']:.{digits}f} (min {s['min']:.{digits}f}, "
            f"max {s['max']:.{digits}f}, n {s['n']})")


# Three decimals, or "-".
def num(value) -> str:
    return "-" if value is None else f"{value:.3f}"


# Part A report lines: one row per question, then the totals.
def part_a_lines(a: dict) -> list[str]:
    rows = a["questions"]
    lines = ["## Part A (the pass rule): seeded store, real embedder", "",
             (f"Facts saved: {a['saved']}; memories in the store: {a['stored']}; replaced: "
             f"{a['replaced']}."), "",
             "| Q | lang | kind | expect | rank in top 5 | similarity | top-1 | in prompt |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        kind = "negation" if r.get("negation") else "g09" if r.get("g09_style") else ""
        lines.append(f"| {r['id']} | {r['lang']} | {kind} | {r['expect']} | "
                     f"{r['rank'] or 'missed'} | {num(r['similarity'])} | {num(r['top1'])} | "
                     f"{'yes' if r['in_prompt'] else 'no'} |")
    hits = sum(1 for r in rows if r["rank"])
    hinglish = [r for r in rows if r["lang"] == "hinglish"]
    lines += ["", (f"**Recall@5: {hits}/{len(rows)} = {recall_at(rows, 5):.2f}** "
              f"(Hinglish {recall_at(hinglish, 5):.2f} of {len(hinglish)}); "
              f"Recall@1 {recall_at(rows, 1):.2f}; Recall@3 {recall_at(rows, 3):.2f}."),
              (f"Expected fact among the prompt hints (top {a['recall_k']}, similarity >= "
              f"{a['min_similarity']}): {sum(r['in_prompt'] for r in rows)}/{len(rows)}."), "",
              "No-memory questions (recorded, not scored):", "",
              "| X | lang | hints given | best similarity |", "|---|---|---|---|"]
    lines += [f"| {x['id']} | {x['lang']} | {x['hints']} | {num(x['best'])} |"
              for x in a["no_memory"]]
    return lines


# Part B report lines: per message, then the summary.
def part_b_lines(b: dict) -> list[str]:
    lines = ["## Part B (reported): the real write path with the local model", "",
             ("| id | picked by word rule | remember | subject given | expected subject | "
             "write ms |"), "|---|---|---|---|---|---|"]
    for r in b["messages"]:
        lines.append(f"| {r['id']} | {'yes' if r['triggered'] else 'no'} | "
                     f"{r['remember'] if r['remember'] is not None else '-'} | "
                     f"{r['subject'] or '-'} | {r.get('expected_subject') or '(must not store)'} | "
                     f"{r['write_ms']:.0f} |")
    s = b["summary"]
    lines += ["", (f"Facts stored: {s['facts_stored']}/{s['facts']}; facts the word rule did not "
              f"pick: {s['facts_not_picked']}; must-not-store kept out: {s['kept_out']}/"
              f"{s['must_not']} (picked by the word rule: {s['must_not_picked']})."),
              (f"Replacements done (old text gone, new text stored): {s['replaced_ok']}/"
              f"{s['replace_pairs']} ({', '.join(s['replace_detail'])})."),
              (f"Recall@5 on the store built by the write path: {s['recall5']:.2f} "
              f"({s['hits']}/{s['questions']}); memories stored: {s['stored']}."),
              f"Extraction LLM calls: {s['calls']}; providers: {s['providers']}."]
    return lines
