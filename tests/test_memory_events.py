"""Tests for leo/language/memory_events.py (M2.3b): code keeps plans and events out of
memory, unless a preference, habit or yearly word marks a lasting fact. No phrase
here is from the check set."""

from datetime import datetime

import pytest

from leo.language.memory_events import (
    is_plan_or_event,
    names_date_or_time,
    says_lasting,
)

NOW = datetime(2026, 11, 26, 21, 0)


# Dates and times the time parser reads, day-and-month dates, and coming periods.
@pytest.mark.parametrize("text", [
    "Kal mera interview hai.", "I have a call at 4 pm.", "Parso main Nagpur jaunga.",
    "My train is on Sunday.", "Aaj mera dinner bahar hai.", "My exam is on 14 April.",
    "My exam is on April 14.", "Mera result 3rd June ko aayega.", "Next week I start a course.",
    "Agle hafte mera interview hai.", "Is mahine nahi, agle mahine shift karunga."])
def test_plans_and_events_are_found(text):
    assert names_date_or_time(text, NOW) and is_plan_or_event(text, NOW)


# Lasting facts with no date or time are not plans.
@pytest.mark.parametrize("text", ["I live in Nashik.", "Mera bhai doctor hai.",
                                  "I may move someday.", "I play cricket on weekends."])
def test_facts_without_dates_are_not_plans(text):
    assert not is_plan_or_event(text, NOW)


# The approved override: preference, habit and yearly words keep a time-bearing fact.
@pytest.mark.parametrize("text", ["I prefer calls after 4 pm.", "Main roz 7 baje gym jaata hoon.",
                                  "Mere papa ka birthday 9 July ko hai.",
                                  "I walk every day at 6 am.", "Our anniversary is on 2 May."])
def test_lasting_words_override_the_time_rule(text):
    assert names_date_or_time(text, NOW) and says_lasting(text)
    assert not is_plan_or_event(text, NOW)
