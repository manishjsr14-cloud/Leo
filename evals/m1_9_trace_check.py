"""M1.9 real tracing check. Sends one fixed message through the real graph
(local model, real tools on an empty temporary database, never leo_data/) with
tracing on and include_text as in config.yaml (false), then reads the trace back
from Langfuse and writes a new report with the span tree and two verdicts.

  python -m evals.m1_9_trace_check evals/reports/m1.9_trace_check_<date>.md

Rules, fixed before the first run:
- STRUCTURE passes if Langfuse returns exactly one root observation named
  "chat", all observations share its trace id, the names include supervisor,
  productivity, responder, "step 1", "tool:calculate" and at least one
  "llm:..." generation, and the trace tags include the model and prompt versions.
- PRIVACY passes if no field of any observation (every field group the API
  offers, serialised to JSON) contains any of: the message text, "18% of 2450",
  "(18/100)", '"441"', the tool argument key '"expression"', the reply text Leo
  gave, or the start of any system prompt ("You are Leo", "You are the
  supervisor", "productivity agent").
"""

import json
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from leo import cli
from leo.agents.productivity import NAME, productivity_agent
from leo.config import load_config, load_secrets
from leo.graph.builder import build_graph
from leo.llm import gateway
from leo.memory.store import open_db
from leo.ops import tracing
from leo.ops.tracing_setup import setup_tracing
from leo.tools.real.productivity import real_productivity_tools
from leo.tools.registry import by_name

MESSAGE = "what is 18% of 2450"
FIXED_FORBIDDEN = [MESSAGE, "18% of 2450", "(18/100)", '"441"', '"expression"',
                   "You are Leo", "You are the supervisor", "productivity agent"]
NEEDED_NAMES = ["chat", "supervisor", "productivity", "responder", "step 1", "tool:calculate"]
FIELDS = "core,basic,time,io,metadata,model,usage,prompt,metrics,trace_context"


# Read a field by its snake_case or camelCase name.
def get(item: dict, name: str):
    camel = name.split("_")[0] + "".join(p.title() for p in name.split("_")[1:])
    return item.get(name, item.get(camel))


# Fetch the trace's observations, waiting until the count stops changing (up to ~90 s).
def fetch(client, trace_id: str) -> list[dict]:
    seen, stable = [], 0
    for _ in range(30):
        time.sleep(3)
        page = client.api.observations.get_many(trace_id=trace_id, fields=FIELDS, limit=1000)
        items = [o.model_dump(mode="json") for o in page.data]
        stable = stable + 1 if items and len(items) == len(seen) else 0
        seen = items
        if stable >= 2:
            break
    return seen


# The span tree as indented markdown lines: name, type, latency, model, tokens.
def tree_lines(items: list[dict], parent=None, depth=0) -> list[str]:
    lines = []
    children = [o for o in items if get(o, "parent_observation_id") == parent]
    for o in sorted(children, key=lambda o: get(o, "start_time") or ""):
        usage = get(o, "usage_details") or {}
        extra = f" model={get(o, 'model')} tokens={usage}" if get(o, "model") else ""
        lines.append(f"{'  ' * depth}- {get(o, 'name')} ({get(o, 'type')}, "
                     f"latency={get(o, 'latency')}){extra}")
        lines += tree_lines(items, get(o, "id"), depth + 1)
    return lines


# Check the structure rule; returns (passed, explanation).
def structure(items: list[dict], trace_id: str) -> tuple[bool, str]:
    roots = [o for o in items if not get(o, "parent_observation_id")]
    names = [get(o, "name") for o in items]
    tags = {t for o in items for t in (get(o, "tags") or [])}
    missing = [n for n in NEEDED_NAMES if n not in names]
    checks = {
        "one root named chat": len(roots) == 1 and get(roots[0], "name") == "chat",
        "one trace id": {get(o, "trace_id") for o in items} == {trace_id},
        "needed spans present": not missing,
        "an llm generation": any(str(n).startswith("llm:") for n in names),
        "model tag": any(t.startswith("model:") for t in tags),
        "prompt tags": any(t.startswith("prompt:") for t in tags),
    }
    failed = [k for k, ok in checks.items() if not ok]
    return not failed, f"failed checks: {failed}, missing spans: {missing}"


# Check the privacy rule over every field of every observation.
def privacy(items: list[dict], reply: str) -> tuple[bool, str]:
    forbidden = FIXED_FORBIDDEN + ([reply] if reply else [])
    found = [(get(o, "name"), text) for o in items for text in forbidden
             if text in json.dumps(o, ensure_ascii=False)]
    return not found, f"forbidden text found: {found}"


# Run the message, read the trace back, and write the report.
def main() -> None:
    report = Path(sys.argv[1])
    if report.exists():
        sys.exit(f"{report} already exists; earlier reports are never rewritten.")
    config = load_config()
    if not setup_tracing(config, load_secrets()):
        sys.exit("tracing is off (see the warning above); no report written")
    client = tracing.current_tracer().client
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
        conn = open_db(Path(folder) / "leo.db")
        agent = productivity_agent(gateway.chat, by_name(real_productivity_tools(conn)),
                                   config.agent.max_steps)
        graph = build_graph(agents={NAME: agent}, config=config)
        start = time.perf_counter()
        reply, _ = cli.run_turn(graph, [], MESSAGE, False, session_id="m1.9-trace-check")
        wall = time.perf_counter() - start
        conn.close()
    trace_id = tracing.last_trace_id()
    tracing.flush()
    items = fetch(client, trace_id)
    s_ok, s_why = structure(items, trace_id)
    p_ok, p_why = privacy(items, reply.content)
    lines = [f"# M1.9 tracing check — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             (f"include_text: {config.tracing.include_text}. Local model: "
             f"{config.llm.primary.model}. Turn time: {wall:.2f} s."), "",
             f"**STRUCTURE: {'PASS' if s_ok else 'FAIL'}** ({s_why})",
             f"**PRIVACY: {'PASS' if p_ok else 'FAIL'}** ({p_why})", "",
             f"Message: {MESSAGE}", f"Reply: {reply.content}", f"Trace id: {trace_id}",
             f"Observations read back from Langfuse: {len(items)}", "",
             "## Span tree (as read back)", "", *tree_lines(items)]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
