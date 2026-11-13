"""The calculator behind the `calculate` tool. sympy does the maths, never the LLM.

The LLM only copies the user's expression, for example "18% of 2450".
This file rewrites common words and symbols into plain arithmetic, checks
that nothing else is left, and lets sympy work out the number.

Safety: sympy's parser runs Python eval, so the input is checked first.
Only digits, + - * / ( ) . spaces and the allowed function names may remain,
and the parser gets a namespace with no builtins.
"""

import re

import sympy
from sympy.parsing.sympy_parser import parse_expr

MAX_LENGTH = 200
MAX_EXPONENT = 1000  # stops things like 9**9**9 that would hang the laptop
FUNCTIONS = {"sqrt": sympy.sqrt}
ALLOWED = re.compile(r"[0-9a-z+\-*/().\s]+")

# Words and symbols people use, rewritten to Python arithmetic (applied in order).
REWRITES = [
    (r"(?<=\d),(?=\d)", ""),  # 2,45,000 -> 245000
    (r"(\d+(?:\.\d+)?)\s*%\s*of\s*", r"(\1/100)*"),  # 18% of 2450
    (r"(\d+(?:\.\d+)?)\s*%", r"(\1/100)"),  # 18%
    (r"\bdivided\s+by\b", "/"),
    (r"\bmultiplied\s+by\b", "*"),
    (r"\b(?:times|into)\b", "*"),
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),
    (r"[×x]", "*"),
    (r"÷", "/"),
    (r"\^", "**"),
    (r"\bsquare\s+root\s+of\s*(\d+(?:\.\d+)?)", r"sqrt(\1)"),
]

# Names the parser may see. "__builtins__" is emptied so eval cannot reach Python.
GLOBALS = {
    "__builtins__": {},
    "Integer": sympy.Integer,
    "Float": sympy.Float,
    "Rational": sympy.Rational,
    "Symbol": sympy.Symbol,
    "Add": sympy.Add,  # Add, Mul and Pow are used by evaluate=False parsing
    "Mul": sympy.Mul,
    "Pow": sympy.Pow,
}


class CalculatorError(ValueError):
    """The expression is not plain arithmetic Leo can work out."""


# Rewrite words and symbols into arithmetic and check only allowed text is left.
def normalize(expression: str) -> str:
    text = expression.strip().lower().rstrip("?=. ")
    if not text or len(text) > MAX_LENGTH:
        raise CalculatorError(f"expression must be 1 to {MAX_LENGTH} characters")
    for pattern, replacement in REWRITES:
        text = re.sub(pattern, replacement, text)
    if not ALLOWED.fullmatch(text):
        raise CalculatorError(f"not plain arithmetic: {expression!r}")
    unknown = set(re.findall(r"[a-z_]+", text)) - set(FUNCTIONS)
    if unknown:
        raise CalculatorError(f"unknown words in expression: {sorted(unknown)}")
    return text


# Refuse powers with huge or non-numeric exponents before sympy evaluates them.
def _check_powers(tree: sympy.Basic) -> None:
    for node in sympy.preorder_traversal(tree):
        if isinstance(node, sympy.Pow):
            exponent = node.exp
            if not exponent.is_number or abs(float(exponent.evalf())) > MAX_EXPONENT:
                raise CalculatorError(f"exponent too large (max {MAX_EXPONENT})")


# Show a sympy number as text: whole numbers exactly, others to 10 digits.
def format_number(value: sympy.Expr) -> str:
    if not value.is_number or not value.is_finite or not value.is_real:
        raise CalculatorError("the answer is not a finite real number (division by zero?)")
    if value.is_Integer:
        return str(value)
    if value == sympy.Integer(sympy.floor(value)):
        return str(sympy.floor(value))
    return format(float(value), ".10g")


# Work out an expression. Returns what was asked, what sympy computed and the result.
def calculate(expression: str) -> dict:
    text = normalize(expression)
    try:
        tree = parse_expr(text, local_dict=dict(FUNCTIONS), global_dict=dict(GLOBALS),
                          evaluate=False)
        _check_powers(tree)
        value = sympy.simplify(tree)
    except CalculatorError:
        raise
    except Exception as error:  # syntax errors from the parser, e.g. "2 +"
        raise CalculatorError(f"could not read the expression: {expression!r}") from error
    return {"expression": expression, "computed": text, "result": format_number(value)}
