"""A check on calculate: every number must come from the user's message (M1.8).

M1.8 run1: for "What is 15% of 3200?" the model sent calculate("15% of 320-0")
and the reply said 48. The calculator is exact, but only on what it is given.
Before calculate runs, each number in the expression must be one the user
wrote, either as digits or as words read by leo/language/numbers.py ("dedh
hazaar" = 1500), or 100 when the message says "%" or "percent". Otherwise
the call is refused with a ToolError, so the model sees the error and can
copy the expression again.
"""

import re
from fractions import Fraction

from leo.language.numbers import MULTIPLIERS, number_at, tokens
from leo.tools.base import Tool, ToolError

NUMBER = re.compile(r"\d+(?:\.\d+)?")


# Every number in the user's message: digit strings and numbers in words.
def message_numbers(text: str) -> set[Fraction]:
    found = {Fraction(n) for n in NUMBER.findall(text.replace(",", ""))}
    words = tokens(text)
    for i in range(len(words)):
        read = number_at(words, i)
        if read is None:
            continue
        value, after = read
        found.add(value)
        if after < len(words) and words[after] in MULTIPLIERS:   # "dedh hazaar" = 1500
            found.add(value * MULTIPLIERS[words[after]])
    if "%" in text or "percent" in text.lower():
        found.add(Fraction(100))
    return found


# The numbers in an expression that are not in the user's message.
def foreign_numbers(expression: str, text: str) -> list[str]:
    allowed = message_numbers(text)
    return [n for n in NUMBER.findall(expression.replace(",", "")) if Fraction(n) not in allowed]


# A copy of the calculate tool whose check refuses numbers the user did not write.
def guard_calculate(tools: dict[str, Tool], text: str) -> dict[str, Tool]:
    tool = tools.get("calculate")
    if tool is None:
        return tools

    # Refuse an expression with a number that is not in the message.
    def check(args) -> None:
        if tool.check is not None:
            tool.check(args)
        bad = foreign_numbers(args.expression, text)
        if bad:
            raise ToolError(f"numbers {bad} are not in the user's message; copy the "
                            "user's expression exactly")

    return {**tools, "calculate": tool.model_copy(update={"check": check})}
