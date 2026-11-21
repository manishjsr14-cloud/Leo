"""M1.8 latency probe: what takes the time before the first token? DESKTOP ONLY.

Sends the same requests straight to Ollama's /api/chat (no Leo gateway), asking
for one output token, so the wall time is close to the time to the first token:
  A. prompts of about 15, 300 and 1,200 tokens ("word" repeated), no schema;
  B. the real productivity agent step: its rendered prompt and a user message,
     once WITHOUT and once WITH the step schema (Ollama `format`, the JSON
     schema Leo sends for every agent step).
Each request runs REPEATS times, with a new last word so no prompt cache is hit
across sizes (B repeats the same text on purpose: the same call both ways).
Records Ollama's own load and prompt-evaluation times and the wall time.

  python -m evals.m1_8_latency_probe evals/reports/m1.8_latency_probe_<date>.md

Results are for the machine in the header only. Figures from the desktop
(RTX 3060) are never quoted as laptop results. No personal data is used.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

from evals.machine import machine_line
from leo.agents.loop import describe_tools
from leo.agents.productivity import PROMPT
from leo.agents.step_schema import step_model
from leo.config import load_config
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.registry import by_name

REPEATS = 3
SIZES = [5, 300, 1200]


# One request with one output token: (wall s, load s, prompt tokens, prompt eval s).
def one_call(messages: list[dict], schema: dict | None) -> tuple:
    primary = load_config().llm.primary
    body = {"model": primary.model, "stream": False, "think": False, "messages": messages,
            "options": {"num_ctx": primary.num_ctx, "num_predict": 1}}
    if schema is not None:
        body["format"] = schema
    start = time.perf_counter()
    reply = httpx.post(f"{primary.base_url}/api/chat", json=body, timeout=120).json()
    return (time.perf_counter() - start, reply["load_duration"] / 1e9,
            reply["prompt_eval_count"], reply["prompt_eval_duration"] / 1e9)


# One report row.
def row(label: str, attempt: int, found: tuple) -> str:
    wall, load, tokens, evaluate = found
    return f"| {label} | {attempt} | {tokens} | {wall:.2f} | {load:.2f} | {evaluate:.3f} |"


# Write a new report; refuse to overwrite an earlier one.
def main() -> None:
    report = Path(sys.argv[1])
    if report.exists():
        sys.exit(f"{report} already exists; earlier reports are never rewritten.")
    rows = []
    for size in SIZES:
        for attempt in range(1, REPEATS + 1):
            text = "word " * size + str(attempt)
            rows.append(row(f"A: {size} words, no schema", attempt,
                            one_call([{"role": "user", "content": text}], None)))
    tools = by_name(mock_productivity_tools([]))
    step = [{"role": "system", "content": PROMPT.render(tools=describe_tools(tools),
                                                        task="add bread")},
            {"role": "user", "content": "Add bread to my tasks"}]
    schema = step_model(tools, first_step=True).model_json_schema()
    for attempt in range(1, REPEATS + 1):
        rows.append(row("B: agent step, no schema", attempt, one_call(step, None)))
        rows.append(row("B: agent step, step schema", attempt, one_call(step, schema)))
    model = load_config().llm.primary.model
    lines = [f"# M1.8 latency probe — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             machine_line(),
             "**Desktop-only figures: never compare with or quote as laptop results.**",
             (f"Model: {model}; one output token per request; direct Ollama /api/chat "
              f"(no Leo gateway); step schema size {len(json.dumps(schema))} characters."),
             "", "| request | try | prompt tokens | wall s | load s | prompt eval s |",
             "|---|---|---|---|---|---|", *rows]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
