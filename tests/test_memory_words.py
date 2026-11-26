"""Tests for leo/language/memory_words.py (M2.3, M2.3b): the code rules that pick messages
for the memory extraction step, so most turns make no extra LLM call."""

import pytest

from leo.language.memory_words import (
    fact_text,
    has_update_cue,
    is_personal_question,
    is_question,
    is_request,
    worth_remembering,
)

# Lasting facts and preferences in the forms the rule knows (none from the check set).
FACTS = [
    "I am a teacher.", "I'm vegetarian.", "I like jazz music.", "I hate long calls.",
    "I prefer tea over coffee.", "I live in Nashik.", "I work night shifts.",
    "I don't eat eggs.", "My dog's name is Bruno.", "I don't drink cola anymore.",
    "Meri mummy ka naam Sunita hai.", "Main Nagpur se hoon.", "Mujhe jazz pasand hai.",
    "Mujhe dust se allergy hai.", "Main anda nahi khata.",
    "Maine cigarette chhod di hai.", "Maine gym jaana chod diya.",  # M2.3 fix round
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


# M2.3b: first-person statements are picked even without a known fact form
# (none from the check set).
@pytest.mark.parametrize("text", ["I drive a red scooter.", "I support Chennai in the IPL.",
                                  "I use an Android phone.", "I mostly cook at home.",
                                  "Mere bhai ka naam Rohit hai.", "Main tabla bajata hoon."])
def test_first_person_statements_are_picked(text):
    assert worth_remembering(text)


# M2.3b: a first-person request is not a fact.
@pytest.mark.parametrize("text", ["Remind me to pay the bill.", "Mera schedule batao.",
                                  "Mujhe ek chai chahiye.", "Please add my gym session.",
                                  "Mere notes dikhao."])
def test_first_person_requests_are_not_picked(text):
    assert is_request(text) and not worth_remembering(text)


# M2.3b update cues; a fact without one is not an update.
@pytest.mark.parametrize("text, cue", [
    ("I don't smoke anymore.", True), ("I no longer live in Nashik.", True),
    ("I moved to Indore.", True), ("Maine cycling chhod di.", True),
    ("Ab main chai nahi peeta.", True), ("I also like jazz.", False),
    ("Meri behen Nagpur mein hai.", False)])
def test_update_cues(text, cue):
    assert has_update_cue(text) is cue


# M2.3b recall gate: a question with a first-person word.
@pytest.mark.parametrize("text, personal", [
    ("What's my shoe size?", True), ("Do I have a cat?", True), ("Mujhe kya pasand hai?", True),
    ("Will it rain tomorrow, should I take an umbrella?", True),
    ("Main kahan rehta hoon?", True), ("Meri mummy kahan hain?", True),
    ("Will it rain tomorrow?", False), ("Aaj ki news kya hai?", False),
    ("I live in Nashik.", False)])
def test_personal_question_gate(text, personal):
    assert is_personal_question(text) is personal


# Known limit (M2.3b): the Hinglish "is" ("this") reads as the English question
# word, so a statement that starts with it is never stored.
def test_hinglish_is_reads_as_a_question():
    assert is_question("Is saal main Goa ja raha hoon.")
    assert not worth_remembering("Is saal main Goa ja raha hoon.")
