"""M1 cleanup item 3: time to first token of the first user turn, with and
without the warm-up (leo/llm/warmup.py). LAPTOP check, real local model.

  python -m evals.m1_cleanup_warmup_check evals/reports/m1_cleanup_warmup_check_<date>.md

Each of PAIRS pairs runs two cold starts, in this order:
  without: unload the model from Ollama, then run the first user turn;
  with:    unload the model, run warm_up(), then run the same first turn.
"Unload" asks Ollama to drop the model (keep_alive 0) and waits until
/api/ps no longer lists it. The first turn is L04 of
evals/scenarios/m1_8_language_turns.yaml ("Add bread to my tasks") through
the real graph on MOCK tools, as in the eval suite. Recorded: the first LLM
call's time to first token (the gateway's first_token_s), the turn's wall
time and the warm-up's own time. Writes a new report; never overwrites one.
"""

import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import yaml

from evals.m1_6_parser_check import git_state
from evals.machine import machine_line
from evals.run_eval import run_turn
from leo.config import load_config
from leo.llm.warmup import warm_up

PAIRS = 3
TURN_FILE = Path("evals/scenarios/m1_8_language_turns.yaml")
TURN_ID = "L04"


# Ask Ollama to unload the model and wait until it is gone (at most 60 s).
def unload(base_url: str, model: str) -> None:
    httpx.post(f"{base_url}/api/generate", json={"model": model, "keep_alive": 0}, timeout=60)
    for _ in range(60):
        loaded = httpx.get(f"{base_url}/api/ps", timeout=10).json().get("models", [])
        if not any(m["name"].split(":")[0] == model.split(":")[0] for m in loaded):
            return
        time.sleep(1)
    raise RuntimeError(f"{model} is still loaded after 60 s")


# One cold start: unload, optionally warm up, run the first turn. Returns a row.
def cold_start(config, data: dict, turn: dict, warm: bool) -> dict:
    primary = config.llm.primary
    unload(primary.base_url, primary.model)
    warm_s = warm_up(config) if warm else None
    result = run_turn(turn, data, turn["lang"], config)
    first = result["calls"][0] if result["calls"] else {}
    return {"mode": "with" if warm else "without", "warm_s": warm_s,
            "first_token_s": first.get("first_token_s"), "provider": first.get("provider"),
            "turn_s": result["wall"], "reply": result["reply"]}


# "1.23" or "-".
def num(value) -> str:
    return "-" if value is None else f"{value:.2f}"


# The report lines.
def report(rows: list[dict], config) -> list[str]:
    lines = [f"# M1 cleanup warm-up check — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             machine_line(), f"Commit: {git_state()}.",
             (f"Local model: {config.llm.primary.model}. First turn: {TURN_FILE.as_posix()} "
              f"{TURN_ID}, mock tools. {PAIRS} pairs; the model is unloaded before every run."),
             "", "## Summary", "",
             "| mode | runs | first token s (avg / min / max) | turn s (avg) |", "|---|---|---|---|"]
    for mode in ("without", "with"):
        firsts = [r["first_token_s"] for r in rows if r["mode"] == mode and r["first_token_s"]]
        turns = [r["turn_s"] for r in rows if r["mode"] == mode]
        spread = (f"{sum(firsts) / len(firsts):.2f} / {min(firsts):.2f} / {max(firsts):.2f}"
                  if firsts else "-")
        lines.append(f"| {mode} warm-up | {len(turns)} | {spread} | "
                     f"{sum(turns) / len(turns):.2f} |")
    lines += ["", "## Runs", "",
              "| pair | mode | warm-up s | first token s | provider | turn s | reply |",
              "|---|---|---|---|---|---|---|"]
    lines += [f"| {i // 2 + 1} | {r['mode']} | {num(r['warm_s'])} | {num(r['first_token_s'])} | "
              f"{r['provider']} | {r['turn_s']:.2f} | {r['reply']} |" for i, r in enumerate(rows)]
    return lines


# Run the pairs and write the report.
def main() -> None:
    out = Path(sys.argv[1])
    if out.exists():
        sys.exit(f"{out} already exists; earlier reports are never rewritten.")
    config = load_config()
    data = yaml.safe_load(TURN_FILE.read_text(encoding="utf-8"))
    turn = next(t for t in data["turns"] if t["id"] == TURN_ID)
    rows = []
    for pair in range(PAIRS):
        for warm in (False, True):
            rows.append(cold_start(config, data, turn, warm))
            print(f"pair {pair + 1} {rows[-1]['mode']}: {num(rows[-1]['first_token_s'])} s",
                  flush=True)
    sys.stdout.reconfigure(encoding="utf-8")
    out.write_text("\n".join(report(rows, config)) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
