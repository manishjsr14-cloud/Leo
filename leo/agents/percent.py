""""X% of Y" questions: code writes the calculate expression (M1 exit check, K05).

M1.8 L08 / M1.10 K05: for "What is 15% of 3200?" the model typed the
expression as "15% of 320iger"; the number check refused it and a retry was
needed. Now code builds "15% of 3200" from the two numbers in the message,
so the model types nothing. Forms read: "15% of 3200", "15 percent of 3,200",
"3200 ka 15%", "3200 ke 15 percent". The message must hold exactly those two
numbers, so "15% of 3200 plus 50" is left to the model as before.
"""

import re

NUMBER = r"(\d+(?:\.\d+)?)"
PERCENT = r"\s*(?:%|percent|pratishat)"
X_OF_Y = re.compile(NUMBER + PERCENT + r"\s+(?:of|ka|ki|ke)\s+" + NUMBER)
Y_KA_X = re.compile(NUMBER + r"\s+(?:ka|ki|ke|of)\s+" + NUMBER + PERCENT)


# The expression "X% of Y" for a message asking for a percentage of a number, or None.
def percent_expression(text: str) -> str | None:
    plain = text.lower().replace(",", "")
    numbers = re.findall(NUMBER, plain)
    found = X_OF_Y.search(plain)
    if found is not None:
        part, whole = found.groups()
    else:
        found = Y_KA_X.search(plain)
        if found is None:
            return None
        whole, part = found.groups()
    if sorted(numbers) != sorted([part, whole]):
        return None
    return f"{part}% of {whole}"
