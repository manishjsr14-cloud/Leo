"""Tests for leo/language/calendar_words.py: cancel and move words."""

from leo.language.calendar_words import asks_to_cancel, asks_to_create, asks_to_move


def test_cancel_words_and_phrase():
    for text in ("Saturday ka gym cancel kar do", "gym hata do", "meeting hatao",
                 "Saturday subah clear kar do", "delete the call", "remove gym"):
        assert asks_to_cancel(text), text
    for text in ("Kal subah 10 baje Rahul ke saath meeting daal do", "hata hua plan"):
        assert not asks_to_cancel(text), text


def test_move_words():
    for text in ("Move my 3 pm meeting", "meeting shift kar do", "time badal do",
                 "change the call"):
        assert asks_to_move(text), text
    assert not asks_to_move("3 baje wali meeting 5 baje kar do")  # two times, no word


def test_create_words():
    for text in ("workshop add karo", "meeting daal do", "call rakh do", "reminder laga do",
                 "schedule a call", "trip plan kar do", "book a slot"):
        assert asks_to_create(text), text
    assert not asks_to_create("3 baje wali meeting 5 baje kar do")
