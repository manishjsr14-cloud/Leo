"""Tests for leo/language/memory_words.py (M2.3): the code rule that picks messages
for the memory extraction step, so most turns make no extra LLM call."""

import pytest

from leo.language.memory_words import fact_text, is_question, worth_remembering

# Lasting facts and preferences in the forms the rule knows (none from the check set).
FACTS = [
    "I am a teacher.", "I'm vegetarian.", "I like jazz music.", "I hate long calls.",
    "I prefer tea over coffee.", "I live in Nashik.", "I work night shifts.",
    "I don't eat eggs.", "My dog's name is Bruno.", "I don't drink cola anymore.",
    "Meri mummy ka naam Sunita hai.", "Main Nagpur se hoon.", "Mujhe jazz pasand hai.",
    "Mujhe dust se allergy hai.", "Main anda nahi khata.",
]
REMEMBER = ["Remember that the gate code is in the blue diary.",
            "Yaad rakhna, gaadi ki service March mein hoti hai.",
            "Gaadi ki service March mein hoti hai, yaad rakhna."]
QUESTIONS = ["Do I like jazz?", "What is my dog's name", "Meri mummy ka naam kya hai",
             "Main kahan rehta hoon?", "Am I vegetarian", "Mera blood group kaunsa hai"]
COMMANDS = ["add milk to my tasks", "Kal subah 10 baje Rahul ke saath meeting daal do",
            "Cancel my dentist appointment", "Will it rain in Pune tomorrow",
            "Set a timer for 10 minutes", "Note kar lo ki doodh lena hai"]


# Fact forms and "remember" / "yaad rakhna" messages are picked.
@pytest.mark.parametrize("text", FACTS + REMEMBER)
def test_facts_and_remember_messages_are_picked(text):
    assert worth_remembering(text)


# Questions are never picked, with or without "?".
@pytest.mark.parametrize("text", QUESTIONS)
def test_questions_are_never_picked(text):
    assert is_question(text)
    assert not worth_remembering(text)


# Ordinary requests are not picked, so they make no extraction call.
@pytest.mark.parametrize("text", COMMANDS)
def test_commands_are_not_picked(text):
    assert not worth_remembering(text)


# The stored fact is the user's own words without the "remember" words.
@pytest.mark.parametrize("text, fact", [
    ("Remember that my scooter is red.", "my scooter is red."),
    ("Remember: my scooter is red.", "my scooter is red."),
    ("Yaad rakhna, mujhe gud pasand hai.", "mujhe gud pasand hai."),
    ("Mujhe gud pasand hai, yaad rakhna.", "Mujhe gud pasand hai"),
    ("I live in Nashik.", "I live in Nashik."),
])
def test_fact_text_strips_remember_words(text, fact):
    assert fact_text(text) == fact
