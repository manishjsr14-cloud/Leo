"""Tests for leo/graph/memory_hints.py (M2.3b): hints in the reply prompt, and the
"say you don't know" rule only for a plain personal question (no agent ran)."""

from leo.graph.memory_hints import (
    DONT_KNOW_NOTE,
    MEMORY_NOTE,
    NO_MEMORY_NOTE,
    memory_hints,
)

WEATHER = {"research": {"steps": [{"tool": "weather", "result": {"rain_chance": 80}}]}}


# Not a personal question and no hints: no memory block at all.
def test_no_block_for_other_turns():
    assert memory_hints({"memories": [], "personal_question": False}) is None
    assert memory_hints({}) is None


# A plain personal question with hints: delimited hints and the don't-know rule.
def test_plain_personal_question_gets_hints_and_dont_know():
    block = memory_hints({"memories": ["My car is red."], "personal_question": True})
    content = block["content"]
    assert MEMORY_NOTE in content and "<memories>\n- My car is red.\n</memories>" in content
    assert DONT_KNOW_NOTE in content


# A plain personal question with nothing stored still gets the don't-know rule.
def test_personal_question_without_hints_gets_dont_know():
    content = memory_hints({"memories": [], "personal_question": True})["content"]
    assert NO_MEMORY_NOTE in content and DONT_KNOW_NOTE in content


# The user's case: "Will it rain tomorrow, should I take an umbrella?" with a
# weather result and no matching memory: hints may be passed, but no don't-know rule.
def test_agent_ran_no_dont_know_rule():
    state = {"memories": ["I use an Android phone."], "personal_question": True,
             "agent_results": WEATHER}
    content = memory_hints(state)["content"]
    assert "I use an Android phone." in content and DONT_KNOW_NOTE not in content
    assert memory_hints({"memories": [], "personal_question": True,
                         "agent_results": WEATHER}) is None
