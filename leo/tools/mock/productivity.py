"""Mock productivity tools for tests and evals. They never touch a database.

Each tool returns fixed data and appends a ToolCall to the call log.
calculate uses the real calculator, because it is pure and has no side effects.
"""

import copy
from datetime import datetime, timedelta

from leo.tools.base import Tool, ToolArgs, ToolCall, ToolError
from leo.tools.calculator import CalculatorError, calculate
from leo.tools.productivity_tools import make_tools

# Two fixed open tasks. list_tasks always returns these.
FIXED_TASKS = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Pay electricity bill", "done": False},
]
FIXED_NOTES = [{"id": 1, "text": "Book the Lonavala homestay before Friday"}]
ADDED_TASK_ID = 3  # the id every mock add_task returns
ADDED_NOTE_ID = 2  # the id every mock add_note returns
MOCK_NOW = datetime.fromisoformat("2026-11-14T08:00:00+05:30")  # fixed "now" for timers


# Build the 7 mock productivity tools. Every call is appended to `log`;
# a call that raises ToolError is logged with the error as its result.
def mock_productivity_tools(log: list[ToolCall]) -> list[Tool]:
    # Run `fn`, log the call and its result (or error), and return the result.
    def logged(name: str, fn):
        def run(args: ToolArgs):
            try:
                result = fn(args)
            except ToolError as error:
                log.append(ToolCall(tool=name, args=args.model_dump(mode="json"),
                                    result={"error": str(error)}))
                raise
            log.append(ToolCall(tool=name, args=args.model_dump(mode="json"), result=result))
            return result
        return run

    # Mark a fixed task done, or fail like the real tool for an unknown id.
    def complete_task(args) -> dict:
        for task in FIXED_TASKS:
            if task["id"] == args.task_id:
                return {**task, "done": True}
        raise ToolError(f"no task with id {args.task_id}; use list_tasks for ids")

    # Let sympy work out the expression, as the real tool does.
    def calculate_tool(args) -> dict:
        try:
            return calculate(args.expression)
        except CalculatorError as error:
            raise ToolError(str(error)) from error

    functions = {
        "add_task": lambda a: {"id": ADDED_TASK_ID, "title": a.title, "done": False},
        "list_tasks": lambda a: copy.deepcopy(FIXED_TASKS),
        "complete_task": complete_task,
        "add_note": lambda a: {"id": ADDED_NOTE_ID, "text": a.text},
        "list_notes": lambda a: copy.deepcopy(FIXED_NOTES[: a.limit]),
        "start_timer": lambda a: {
            "label": a.label, "minutes": a.minutes,
            "ends_at": (MOCK_NOW + timedelta(minutes=a.minutes)).isoformat()},
        "calculate": calculate_tool,
    }
    return make_tools({name: logged(name, fn) for name, fn in functions.items()})
