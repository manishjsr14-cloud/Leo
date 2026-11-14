"""Pass rules for evals/m1_5_cli_check.py. Never edited to improve a score:
a new rule is a new version with a change log entry, committed before its run.
"""

# Pass rule v1, committed before the first run. Only turns 1 and 4 are scored;
# turns 2 (Hinglish) and 3 (web search) are recorded only.
# Turn 1: the research agent ran; get_weather succeeded with a place containing
#   "pune" (any case); the reply contains "open-meteo" (any case, which also
#   covers the URL open-meteo.com).
# Turn 4: the productivity agent ran, and the research agent did not run.
#
# Pass rule v2: v1 plus two checks. Turns 1, 3 and 4 are scored; turn 2 is
# recorded only.
# Turn 1: also, a successful get_weather result has a row labelled "tomorrow".
# Turn 3: the productivity agent did not run.
# Change log: v2 added on 2026-11-14 after report 1 (m1.5_cli_check_2026-11-14.md)
# and before report 2. Report 1 passed turn 1 under v1 although get_weather had
# no row for tomorrow, and the web question also ran productivity. v1 is kept
# and still reported; report 1 stays as it was.
RULES = {"v1": {1, 4}, "v2": {1, 3, 4}}


# True when a logged tool call succeeded (its result is not an {"error": ...} dict).
def succeeded(call) -> bool:
    return not (isinstance(call.result, dict) and "error" in call.result)


# The pass rule v1 verdict for one turn (None for a turn v1 does not score).
def verdict_v1(number: int, ran: list[str], tools_run, reply: str) -> bool | None:
    if number == 1:
        weather_ok = any(c.tool == "get_weather" and succeeded(c)
                         and "pune" in c.args.get("place", "").lower() for c in tools_run)
        return "research" in ran and weather_ok and "open-meteo" in reply.lower()
    if number == 4:
        return "productivity" in ran and "research" not in ran
    return None


# The pass rule v2 verdict for one turn (None for a turn v2 does not score).
def verdict_v2(number: int, ran: list[str], tools_run, reply: str) -> bool | None:
    if number == 1:
        tomorrow = any(c.tool == "get_weather" and succeeded(c)
                       and any(d.get("day") == "tomorrow" for d in c.result.get("days", []))
                       for c in tools_run)
        return bool(verdict_v1(number, ran, tools_run, reply)) and tomorrow
    if number == 3:
        return "productivity" not in ran
    return verdict_v1(number, ran, tools_run, reply)


# "PASS", "FAIL" or "-" (not scored) for a report cell.
def cell(ok: bool | None) -> str:
    return "-" if ok is None else ("PASS" if ok else "FAIL")
