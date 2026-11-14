"""Word lists for the Indian time parser (leo/language/time_parser.py).

Kept apart from the parser so each file stays short. All words are lowercase
Roman spellings, with the common variants people type.
"""

# Day words and their offset in days from today ("kal" is decided by tense).
TODAY = {"aaj", "aj", "today"}
TOMORROW = {"tomorrow", "tmrw"}
YESTERDAY = {"yesterday"}
PARSO = {"parso", "parson", "parsoon"}
KAL = {"kal", "kl"}

# "agle Monday", "next Friday".
NEXT_WORDS = {"agle", "agla", "agli", "next"}

# Weekdays, Monday = 0 (as in datetime.weekday()).
WEEKDAYS = {
    0: ["monday", "somvaar", "somvar", "somwar"],
    1: ["tuesday", "mangalvaar", "mangalvar", "mangalwar"],
    2: ["wednesday", "budhvaar", "budhvar", "budhwar"],
    3: ["thursday", "guruvaar", "guruvar", "guruwar", "veervaar"],
    4: ["friday", "shukravaar", "shukravar", "shukrawar"],
    5: ["saturday", "shanivaar", "shanivar", "shaniwar"],
    6: ["sunday", "ravivaar", "ravivar", "raviwar", "itvaar"],
}
WEEKDAY_OF = {word: day for day, words in WEEKDAYS.items() for word in words}
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Parts of the day.
PERIODS = {
    **dict.fromkeys(["subah", "subh", "subha", "subeh", "morning"], "morning"),
    **dict.fromkeys(["dopahar", "dopehar", "dupahar", "afternoon"], "afternoon"),
    **dict.fromkeys(["shaam", "sham", "evening"], "evening"),
    **dict.fromkeys(["raat", "rat", "night"], "night"),
}

# Words that mark the number before them as a clock hour.
HOUR_MARKERS = {"baje", "bje", "baj"}

# Duration units in minutes, for "2 ghante baad" and "15 minute pehle".
UNITS = {
    **dict.fromkeys(["minute", "minutes", "min", "mins", "minat", "mint"], 1),
    **dict.fromkeys(["ghanta", "ghante", "ghanton", "hour", "hours", "hr", "hrs"], 60),
    **dict.fromkeys(["din", "day", "days"], 24 * 60),
}
AFTER_WORDS = {"baad", "mein", "me", "later"}     # "2 ghante baad"
BEFORE_WORDS = {"pehle", "pahle", "before"}       # "15 minute pehle"
IN_WORDS = {"in", "after"}                        # "in 20 minutes"

# Tense signals that decide "kal". Plain words and word endings.
FUTURE_WORDS = {
    "hai", "hain", "hoga", "hogi", "karna", "karni", "karo", "kar", "do", "dena",
    "daal", "dal", "rakhna", "rakho", "jaana", "jana", "milna", "chalana", "uthna",
    "nikalna", "yaad", "remind", "bata", "laga", "lagao", "will",
}
FUTURE_ENDINGS = ("enge", "ega", "egi", "oge", "unga", "ungi")
PAST_WORDS = {
    "tha", "thi", "the", "kiya", "kiye", "gaya", "gayi", "gaye", "hua", "hui",
    "hue", "dekha", "dekhi", "liya", "chuka", "chuki", "was", "did",
}

# Questions the agent can ask back (Hinglish; prompts move to prompts/ in M1.8).
QUESTIONS = {
    "kal": "Kal matlab aane wala kal (tomorrow) ya beeta hua kal (yesterday)?",
    "midnight": "Aadhi raat ke baad 'kal' ya 'parso' saaf nahi hota. Kaunsi date chahiye?",
    "weekday": "Kaunsa {day}: is hafte wala ya agle hafte wala?",
}
