"""The Markdown report of the M2.4 restart check (evals/m2_4_restart_check.py)."""

from datetime import datetime

from evals import m2_4_scoring as sc


# "1234" or "?" for a missing number; seconds with one decimal.
def num(value) -> str:
    return "?" if value is None else str(value)


def secs(value) -> str:
    return "?" if value is None else f"{value:.1f}"


# The result line from the summary variant's parts.
def result_line(parts: list | None) -> str:
    if parts is None:
        return "**Result: NOT MET** (a part of the run did not finish; see below)."
    if all(ok for _, ok in parts):
        return "**Result: PASSED** (every part of the pass rule met, summary variant)."
    return "**Result: NOT MET** (at least one part of the pass rule missed)."


# The after-restart table for one variant: reply, answered, where the fact was.
def restart_rows(run: dict, data: dict) -> list[str]:
    sources = {t["id"]: t["text"] for t in data["before_kill"]}
    out = ["| id | expected | answered | fact was in | reply |", "|---|---|---|---|---|"]
    for t in data["after_restart"]:
        r = run["turns"].get(t["id"])
        if r is None:
            out.append(f"| {t['id']} | {t['expect_any_of'][0]} | not run | - | - |")
            continue
        where = sc.where_found(r, sources[t["from"]], t["expect_any_of"])
        ok = "yes" if sc.answered(r["reply"], t["expect_any_of"]) else "NO"
        out.append(f"| {t['id']} | {', '.join(t['expect_any_of'])} | {ok} | {where} | "
                   f"{r['reply'].replace('|', '/')} |")
    return out


# Per-turn prompt tokens for both variants side by side.
def token_rows(runs: dict, data: dict) -> list[str]:
    out = [("| turn | largest prompt (summary) | largest prompt (no summary) | responder "
           "prompt (summary) | responder prompt (no summary) | summary call tokens / s |"),
           "|---|---|---|---|---|---|"]
    for t in data["before_kill"] + data["after_restart"]:
        a = runs["summary"]["turns"].get(t["id"])
        b = runs["no_summary"]["turns"].get(t["id"])
        ra, rb = (sc.token_row(x) if x else {} for x in (a, b))
        call = (f"{num(ra.get('summary_tokens'))} / {secs(ra.get('summary_s'))}"
                if ra.get("summary_tokens") is not None else "-")
        out.append(f"| {t['id']} | {num(ra.get('largest'))} | {num(rb.get('largest'))} | "
                   f"{num(ra.get('responder'))} | {num(rb.get('responder'))} | {call} |")
    return out


# Totals and summary-call times for each variant.
def total_lines(runs: dict) -> list[str]:
    out = []
    for name, run in runs.items():
        t = sc.token_totals(list(run["turns"].values()))
        times = t["summary_s"]
        timing = (f"; summary calls {t['summary_calls']}, {min(times):.1f}-{max(times):.1f} s, "
                  f"mean {sum(times) / len(times):.1f} s") if times else "; no summary calls"
        out.append(f"- {name}: {t['calls']} LLM calls, prompt tokens {t['all_prompt_tokens']} "
                   f"in all ({t['non_summary_prompt_tokens']} without the summary calls; "
                   f"{t['unknown_token_counts']} calls without a count){timing}")
    return out


# Kill and state evidence for one variant.
def kill_lines(name: str, run: dict) -> list[str]:
    before, after = run["before_kill"] or {}, run["after_restart"] or {}
    return [(f"- {name}: part 1 hard-killed while waiting for input: "
            f"{'yes' if run['part1_killed'] else 'NO'} (exit code {run['part1_exit_code']}); "
            f"part 2 exit code {run['part2_exit_code']}"),
            (f"  - before the kill: {len(before.get('messages', []))} messages, summary "
            f"{'present' if before.get('summary') else 'none'}; after the restart: "
            f"{len(after.get('messages', []))} messages, summary "
            f"{'present' if after.get('summary') else 'none'}; same messages: "
            f"{'yes' if before.get('messages') == after.get('messages') else 'NO'}; "
            f"same summary: {'yes' if before.get('summary') == after.get('summary') else 'NO'}"),
            f"  - summary after the restart: {after.get('summary') or '(none)'!r}"]


# Every turn of the summary variant: agents, tools, times, reply.
def turn_lines(run: dict) -> list[str]:
    out = []
    for tid, r in run["turns"].items():
        tools = ", ".join(c["tool"] for c in r["tool_log"]) or "none"
        out += [f"- {tid}: {r['text']}",
                (f"  - agents: {', '.join(r['agents']) or 'none'}; tools: {tools}; reply shown "
                f"after {secs(r['reply_s'])} s, turn {secs(r['turn_s'])} s; messages after: "
                f"{r['messages_after']}"), f"  - reply: {r['reply']}"]
    return out


# The whole report.
def report(result: dict, data: dict) -> list[str]:
    runs, conv = result["runs"], result["conversation"]
    out = [f"# M2.4 restart check ({datetime.now():%Y-%m-%d %H:%M})", "", result["machine"],
           f"Commit: {result['commit']}.", f"Check set: {result['set']}.",
           (f"Now for every turn: {result['now']}. Local model: {result['model']}. Memory off; "
           "all tools are mocks."),
           (f"Summary settings: summarize_after {conv['summarize_after']}, keep_messages "
           f"{conv['keep_messages']}."),
           f"Databases left by the check: {runs['summary']['db']}, {runs['no_summary']['db']}.",
           "", result_line(runs["summary"]["parts"]), "", "## Pass rule (summary variant)", ""]
    out += [f"- {'met' if ok else 'MISSED'}: {text}" for text, ok in runs["summary"]["parts"]
            or []]
    out += ["", "## Kill and restart", ""]
    for name, run in runs.items():
        out += kill_lines(name, run)
    for name, run in runs.items():
        label = "judged" if name == "summary" else "reported only"
        out += ["", f"## After the restart: {name} ({label})", ""] + restart_rows(run, data)
    out += ["", "## Prompt tokens (reported only)", ""] + total_lines(runs) + [""]
    out += token_rows(runs, data)
    return out + ["", "## Turns (summary variant)", ""] + turn_lines(runs["summary"])
