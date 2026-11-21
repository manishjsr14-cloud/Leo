"""M1.2 real chat check. Runs 4 fixed turns through the real graph and writes
the transcript, time per turn and answering provider to a new report.

  python -m evals.m1_2_cli_check evals/reports/m1.2_cli_check_<date>.md

Uses the same functions as `python -m leo.cli` (split_cloud_prefix, run_turn).
Real local model and Groq; no tools, calendar or personal data.
"""

import sys
import time
from datetime import datetime
from pathlib import Path

from evals.machine import machine_line
from leo import cli
from leo.config import load_config
from leo.graph.builder import build_graph
from leo.llm.gateway import LLMUnavailable

# Fixed before the run: greeting, follow-up that needs turn 1, Hinglish, cloud.
TURNS = [
    "Hi Leo! My name is Arjun.",
    "What is my name?",
    "Aaj bahut thak gaya hoon, ek chhota sa tip do.",
    "use cloud: Summarise our chat so far in one line.",
]


# Run the turns and return the report lines. A failed turn is reported, not hidden.
def run_turns() -> list[str]:
    graph = build_graph()
    history: list = []
    rows, transcript = [], []
    for number, line in enumerate(TURNS, start=1):
        text, cloud = cli.split_cloud_prefix(line)
        start = time.perf_counter()
        try:
            reply, history = cli.run_turn(graph, history, text, cloud)
        except LLMUnavailable as error:  # both models failed: report it
            wall = time.perf_counter() - start
            rows.append(f"| {number} | {cloud} | FAILED | | | | {wall:.2f} |")
            transcript += [f"**You:** {line}", "", f"**Leo:** FAILED: {error!r}", ""]
            continue
        wall = time.perf_counter() - start
        meta = reply.response_metadata
        first = meta.get("first_token_s")
        rows.append(
            f"| {number} | {cloud} | {meta.get('provider')} | {meta.get('model')} | "
            f"{meta.get('fallback_reason')} | {first if first is None else f'{first:.2f}'} | "
            f"{wall:.2f} |"
        )
        transcript += [f"**You:** {line}", "", f"**Leo:** {reply.content}", ""]
    return [
        "## Turns",
        "turn_s is wall time for the whole graph run (supervisor + responder).",
        "",
        "| turn | force_cloud | provider | model | fallback_reason | first_token_s | turn_s |",
        "|---|---|---|---|---|---|---|",
        *rows,
        "",
        "## Transcript",
        "",
        *transcript,
    ]


# Write a new report; refuse to overwrite an earlier one.
def main() -> None:
    report = Path(sys.argv[1])
    if report.exists():
        sys.exit(f"{report} already exists; earlier reports are never rewritten.")
    config = load_config()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = [f"# M1.2 CLI chat check — {stamp}", machine_line(),
              (f"Local model: {config.llm.primary.model}. "
               f"Fallback: {config.llm.fallback.model}. "
               f"max_hops: {config.graph.max_hops}. Agents registered: none."), ""]
    report.write_text("\n".join(header + run_turns()) + "\n", encoding="utf-8")
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
