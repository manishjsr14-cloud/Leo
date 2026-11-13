"""Tests for leo/tools/calculator.py: sympy answers, and unsafe input is refused."""

import pytest

from leo.tools.calculator import CalculatorError, calculate


@pytest.mark.parametrize(
    ("expression", "result"),
    [
        ("18% of 2450", "441"),
        ("2+3*4", "14"),
        ("2^10", "1024"),
        ("(2+3) x 4", "20"),
        ("100 divided by 8", "12.5"),
        ("12 plus 30 minus 2", "40"),
        ("2,45,000 * 2", "490000"),
        ("2.5 * 4", "10"),
        ("0.1 + 0.2", "0.3"),
        ("1/3", "0.3333333333"),
        ("sqrt(144)", "12"),
        ("square root of 2", "1.414213562"),
        ("15% of 1,200?", "180"),
    ],
)
def test_answers_come_from_sympy(expression, result):
    assert calculate(expression)["result"] == result


# The result keeps what was asked and shows what sympy actually computed.
def test_result_shows_expression_and_computed_text():
    out = calculate("18% of 2450")
    assert out == {"expression": "18% of 2450", "computed": "(18/100)*2450", "result": "441"}


def test_division_by_zero_is_a_clear_error():
    with pytest.raises(CalculatorError, match="division by zero"):
        calculate("5/0")


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('dir')",
        "open('x')",
        "a + b",
        "lambda: 1",
        "2 ** 2 ; 3",
        "9^9^9",
        "2^100000",
        "1" * 201,
        "",
        "2 +",
    ],
)
def test_unsafe_or_bad_input_is_refused(expression):
    with pytest.raises(CalculatorError):
        calculate(expression)
