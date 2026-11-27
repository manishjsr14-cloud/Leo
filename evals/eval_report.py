"""Report text for the M1.10 eval suite (evals/run_eval.py): the sampling
settings line, and the Markdown body built from the turn records.
"""

import json
import urllib.request
from collections import Counter

from evals.eval_metrics import table
from evals.eval_v2 import fail_reasons
from evals.m1_8_check_helpers import call_label

SAMPLING_KEYS = ("temperature", "top_k", "top_p", "seed")


# The local model's sampling parameters as Ollama reports them ("" if it cannot be asked).
def ollama_parameters(base_url: str, model: str) -> str:
    body = json.dumps({"model": model}).encode()
    request = urllib.request.Request(f"{base_url}/api/show", data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            text = json.loads(response.read()).get("parameters", "")
    except (OSError, ValueError):
        return ""
    found = [line.split(None, 1) for line in text.splitlines() if line.strip()]
    return ", ".join(f"{k} {v.strip()}" for k, v in (p for p in found if len(p) == 2)
                     if k in SAMPLING_KEYS)


# The header line on temperature and seed. Leo sends the temperature from
# config.yaml (M1 exit check) and no seed (leo/llm/clients.py).
def sampling_line(config) -> str:
    params = ollama_parameters(config.llm.primary.base_url, config.llm.primary.model)
    seed = "set" if "seed" in params else "none set"
    return (f"Sampling: Leo's requests set temperature {config.llm.primary.temperature} "
            f"(config.yaml) and no seed. "
            f"{config.llm.primary.model} parameters reported by Ollama: "
            f"{params or 'could not be read'}; seed: {seed}. "
            f"Groq fallback: provider default temperature, no seed.")


# "ok", "FAIL" or "-" (not scored) for one check.
def mark(value) -> str:
    return "-" if value is None else "ok" if value else "FAIL"


# One list section, e.g. the known failing turns, with each turn's reasons
# (a failed language check included, M1 cleanup item 2).
def turn_list(title: str, records: list[dict], scorer: str = "v1") -> list[str]:
    lines = [f"## {title} ({len(records)})", ""]
    for r in records:
        why = "; ".join(fail_reasons(r, scorer))
        source = f" [from {r['from']}]" if r.get("from") else ""
        lines.append(f"- {r['key']}{source}: {why or 'all checks pass'}")
    return lines + ([""] if records else ["- none", ""])


# Detail lines for one turn.
def details(r: dict) -> list[str]:
    lines = [f"### {r['key']} ({r['lang']}): {r['verdict']}", "", f"**You:** {r['text']}", "",
             f"**Leo:** {r['reply']}", "", f"Language: {r['lang_why']}",
             f"Language (v2): {r['lang_v2_why']}; verdict with v2: {r['verdict_v2']}",
             f"Plan: {r['plan']}; stops: {r['stops'] or 'no agent run'}",
             "LLM calls: " + ", ".join(call_label(c) for c in r["calls"]), "", "Tool calls:"]
    lines += [f"- `{s['tool']}({s['args']})` -> `{s['result']}`" for s in r["steps"]] or ["- none"]
    lines += ["", "Mock tools' log (calls that ran):"]  # M2.3c
    lines += [f"- `{c['tool']}({c['args']})` -> `{c['result']}`"
              for c in r.get("tool_log", [])] or ["- none"]
    lines += [f"- tool check failed: {f}" for f in r["tool_fails"]]
    lines += [f"- reply check failed: {f}" for f in r["reply_fails"]]
    return lines + [""]


# The report body after the header: summary, metrics, lists, table, details.
def body(records: list[dict], metrics: dict, comparison: list[str]) -> list[str]:
    counts = Counter(r["verdict"] for r in records)
    refused = Counter(c.split(" (", 1)[1].rstrip(")").split(":")[0]
                      for r in records for c in r["refused"])
    lines = ["## Summary", "",
             (f"Turns: {len(records)}. pass {counts['pass']}, fail (new) {counts['fail']}, "
              f"known_failing {counts['known_failing']}, fixed {counts['fixed']}."),
             (f"Refused calls: {sum(refused.values())} "
              f"({', '.join(f'{k}: {v}' for k, v in refused.items()) or 'none'})."), "",
             "## Metrics", "",
             ("All turns are counted, known failing ones included. A '-' check is not scored "
              "for that turn (no tool expectations beyond the plan)."), "", *table(metrics), ""]
    lines += turn_list("New failures", [r for r in records if r["verdict"] == "fail"])
    lines += turn_list("New failures with scorer v2",
                       [r for r in records if r["verdict_v2"] == "fail"], "v2")
    lines += turn_list("Known failing", [r for r in records if r["verdict"] == "known_failing"])
    lines += turn_list("Fixed (known failing, now passing)",
                       [r for r in records if r["verdict"] == "fixed"])
    with_refused = [r for r in records if r["refused"]]
    lines += [f"## Refused calls ({sum(len(r['refused']) for r in records)})", ""]
    lines += [f"- {r['key']}: {', '.join(r['refused'])}" for r in with_refused] or ["- none"]
    lines += ["", "## Turns", "",
              ("| turn | lang | verdict | verdict v2 | routing | tools | reply | refused | "
               "llm_calls | turn_s |"),
              "|---|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r['key']} | {r['lang']} | {r['verdict']} | {r['verdict_v2']} | "
              f"{mark(r['routing_ok'])} | "
              f"{mark(r['tools_ok'])} | {mark(r['reply_ok'])} | {len(r['refused'])} | "
              f"{r['llm_calls']} | {r['turn_s']:.1f} |" for r in records]
    if comparison:
        lines += ["", "## Comparison", "", *comparison]
    lines += ["", "## Details", ""]
    return lines + [line for r in records for line in details(r)]
