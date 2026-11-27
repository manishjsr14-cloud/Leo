"""Scoring for the M2.3c check (evals/scenarios/m2_3c_statement_set.yaml).

Every count is read from the mock tools' log of each turn (each tool call that
actually ran), never from the LLM text. A write is any tool not marked
read_only (leo/tools/base.py). A request's write call "ran" when it is in the
log with a result that is not an error.
"""

from leo.tools.mock.calendar import mock_calendar_tools
from leo.tools.mock.productivity import mock_productivity_tools
from leo.tools.mock.research import mock_research_tools
from leo.tools.registry import by_name

# The names of every mock tool that is a write (not read_only).
WRITES = {name for name, tool in by_name(mock_calendar_tools([]) + mock_productivity_tools([])
                                         + mock_research_tools([])).items()
          if not tool.read_only}


# The write calls in one turn's tool log.
def write_calls(log: list[dict]) -> list[dict]:
    return [c for c in log if c["tool"] in WRITES]


# True when `tool` ran in the log with a result that is not an error.
def ran_ok(log: list[dict], tool: str) -> bool:
    return any(c["tool"] == tool and not (isinstance(c["result"], dict) and "error" in c["result"])
               for c in log)


# The pass-rule parts this check can judge: (text, met). The M1.10 part is
# judged from its own report; the t09 reply is the user's judgement.
def parts(data: dict, records: dict) -> list[tuple[str, bool]]:
    statements = {m["id"]: len(records[m["id"]]["tool_log"]) for m in data["statements"]}
    questions = {m["id"]: len(write_calls(records[m["id"]]["tool_log"]))
                 for m in data["questions"]}
    missed = [m["id"] for m in data["requests"]
              if not ran_ok(records[m["id"]]["tool_log"], m["expect_write"])]
    t09 = records["t09"]
    called = {k: v for k, v in statements.items() if v}
    wrote = {k: v for k, v in questions.items() if v}
    return [
        ((f"statements: {sum(statements.values())} tool calls (max 0; by message: "
         f"{called or 'none'})"), not called),
        ((f"questions: {sum(questions.values())} write calls (max 0; by message: "
         f"{wrote or 'none'})"), not wrote),
        ((f"requests: expected write call ran for {len(data['requests']) - len(missed)} of "
         f"{len(data['requests'])} (missed: {missed or 'none'})"), not missed),
        ((f"t09: agents {t09['agents'] or 'none'}, {len(t09['tool_log'])} tool calls "
         "(expected no agent, 0 tool calls; the reply is the user's judgement)"),
         not t09["agents"] and not t09["tool_log"]),
    ]
