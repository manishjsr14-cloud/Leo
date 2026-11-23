"""Metrics for the M1.10 eval suite (architecture section 11.3, the ones that
apply in M1): each metric for all turns, Hinglish turns and English turns.

Rates are [passed, counted]; a turn whose check is None (not scored) is not
counted. Number metrics give avg, p50, p95 and max per turn, with p50/p95 by
nearest rank (the value at position ceil(p * n) in sorted order).
Only the "turn seconds" row depends on the machine (TIMING_ROWS).
"""

import math

GROUPS = ("all", "hinglish", "en")
RATES = {  # metric name -> the record key it counts
    "routing accuracy": "routing_ok",
    "tool-call accuracy": "tools_ok",
    "reply checks (all)": "reply_ok",
    "reply: language": "lang_ok",
    "reply: clock times match tools": "clock_ok",
    "reply: no JSON": "json_ok",
    "reply: no invented results": "invented_ok",
    "turn passed (all checks)": "passed",
}
NUMBERS = {  # metric name -> how to read it from a record
    "LLM calls per turn": lambda r: r["llm_calls"],
    "refused calls per turn": lambda r: len(r["refused"]),
    "fallback (Groq) calls per turn": lambda r: r["fallback_calls"],
    "turn seconds": lambda r: r["turn_s"],
}
TIMING_ROWS = {"turn seconds"}


# The records of one group ("all", "hinglish" or "en").
def group(records: list[dict], name: str) -> list[dict]:
    return records if name == "all" else [r for r in records if r["lang"] == name]


# Value at nearest rank p (0 < p <= 1) of a non-empty list.
def nearest_rank(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[max(1, math.ceil(p * len(ordered))) - 1]


# avg/p50/p95/max/n of a list of numbers, or None when it is empty.
def summary(values: list[float]) -> dict | None:
    if not values:
        return None
    return {"avg": sum(values) / len(values), "p50": nearest_rank(values, 0.5),
            "p95": nearest_rank(values, 0.95), "max": max(values), "n": len(values),
            "total": sum(values)}


# All metrics: {"rates": {metric: {group: [passed, counted]}}, "numbers": {...}}.
def compute(records: list[dict]) -> dict:
    rates, numbers = {}, {}
    for name, key in RATES.items():
        rates[name] = {}
        for g in GROUPS:
            counted = [r[key] for r in group(records, g) if r[key] is not None]
            rates[name][g] = [sum(bool(v) for v in counted), len(counted)]
    for name, read in NUMBERS.items():
        numbers[name] = {g: summary([read(r) for r in group(records, g)]) for g in GROUPS}
    return {"rates": rates, "numbers": numbers}


# "41/42 (97.6 %)" or "-" for an empty count.
def rate_text(cell: list[int]) -> str:
    passed, counted = cell
    return f"{passed}/{counted} ({100 * passed / counted:.1f} %)" if counted else "-"


# "avg 3.1, p50 3, p95 7, max 7" or "-".
def number_text(cell: dict | None) -> str:
    if cell is None:
        return "-"
    return (f"avg {cell['avg']:.1f}, p50 {cell['p50']:g}, p95 {cell['p95']:g}, "
            f"max {cell['max']:g}")


# Markdown table of all metrics, one column per group.
def table(metrics: dict) -> list[str]:
    lines = ["| metric | all | hinglish | en |", "|---|---|---|---|"]
    for name, cells in metrics["rates"].items():
        lines.append(f"| {name} | " + " | ".join(rate_text(cells[g]) for g in GROUPS) + " |")
    for name, cells in metrics["numbers"].items():
        lines.append(f"| {name} | " + " | ".join(number_text(cells[g]) for g in GROUPS) + " |")
    return lines
