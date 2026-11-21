"""Helpers for evals/m1_8_check.py: an LLM wrapper that records timings and
prompt sizes, the per-node prompt-size summary, and reading the baseline report.
"""

from pathlib import Path
from statistics import mean

from leo.graph.supervisor import SupervisorPlan
from leo.llm import gateway


class TimedChat:
    """Wraps gateway.chat and records each call: node, provider, reply, tokens, times."""

    def __init__(self):
        self.calls: list[dict] = []

    # Call the real gateway and record who called it and how long it took.
    def __call__(self, messages, output_model=None, force_cloud=False):
        result = gateway.chat(messages, output_model, force_cloud)
        if isinstance(output_model, type) and issubclass(output_model, SupervisorPlan):
            node = "supervisor"
        elif output_model is None:
            node = "responder"
        else:
            node = "agent"
        self.calls.append({
            "node": node, "provider": result.provider, "fallback": result.fallback_reason,
            "text": result.text, "prompt_tokens": result.prompt_tokens,
            "first_token_s": result.first_token_s, "total_s": result.total_s})
        return result


# Short label for one call, e.g. "agent:ollama 812 tok 1.9/2.4 s".
def call_label(call: dict) -> str:
    reason = f" ({call['fallback']})" if call["fallback"] else ""
    first = call["first_token_s"]
    first_text = f"{first:.1f}" if first is not None else "?"
    return (f"{call['node']}:{call['provider']}{reason} {call['prompt_tokens']} tok "
            f"{first_text}/{call['total_s']:.1f} s")


# Average prompt tokens, time to first token and total time per node, over all turns.
def node_summary(all_calls: list[dict]) -> list[str]:
    lines = [("| node | calls | avg prompt tokens | max prompt tokens | avg first token s "
              "| avg total s |"), "|---|---|---|---|---|---|"]
    for node in ("supervisor", "agent", "responder"):
        calls = [c for c in all_calls if c["node"] == node and c["provider"] == "ollama"]
        tokens = [c["prompt_tokens"] for c in calls if c["prompt_tokens"] is not None]
        firsts = [c["first_token_s"] for c in calls if c["first_token_s"] is not None]
        if not calls:
            lines.append(f"| {node} | 0 | - | - | - | - |")
            continue
        lines.append(
            f"| {node} | {len(calls)} | {mean(tokens):.0f} | {max(tokens)} | "
            f"{mean(firsts):.2f} | {mean(c['total_s'] for c in calls):.2f} |"
            if tokens and firsts else f"| {node} | {len(calls)} | ? | ? | ? | ? |")
    return lines


# LLM calls per turn id from the table of an earlier report of this check.
def baseline_calls(report: Path) -> dict[str, int]:
    rows = [line for line in report.read_text(encoding="utf-8").splitlines()
            if line.startswith("|")]
    header = [cell.strip() for cell in rows[0].strip("|").split("|")]
    at_id, at_calls = header.index("turn"), header.index("llm_calls")
    found = {}
    for row in rows[2:]:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if len(cells) == len(header) and cells[at_calls].isdigit():
            found[cells[at_id]] = int(cells[at_calls])
    return found


# The baseline report's "Machine:" line, so a run is never compared across machines.
def baseline_machine(report: Path) -> str:
    lines = report.read_text(encoding="utf-8").splitlines()
    return next((line for line in lines if line.startswith("Machine:")), "Machine: none")
