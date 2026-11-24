"""Hindi number words 13 to 99 in Roman script, for amounts only (M1 cleanup item 5).

leo/language/numbers.py reads these in parse_amount ("pachaas hazaar" = 50000).
They are never read as clock hours: the time parser uses numbers.number_at,
which knows only one to twelve, so "bees minute" or "tees baje" stay as before.
One to twelve and sau/hazaar/lakh/crore live in numbers.py.
"saath"/"sath" also means "with" ("Rahul ke saath"), so it counts as 60 only
right before a multiplier or a rupee word (see numbers.amount_at).
"tera" (also "your") is left out; 13 is "terah". "bees" (also English) is read
as 20 and listed with the other words that can mean something else in the
M1.6 parser report.
"""

# Number -> common Roman spellings.
SPELLINGS = {
    13: ["terah"], 14: ["chaudah", "chauda"], 15: ["pandrah", "pandra"],
    16: ["solah", "sola"], 17: ["satrah", "satra"], 18: ["atharah", "athara", "attharah"],
    19: ["unnis", "unees"], 20: ["bees", "bis"], 21: ["ikkis", "ikkees"],
    22: ["baais", "bais"], 23: ["teis", "teyis"], 24: ["chaubis", "chaubees"],
    25: ["pachchis", "pachees", "pachis"], 26: ["chhabbis", "chabbis"],
    27: ["sattais", "sattaees"], 28: ["atthais", "athaais"], 29: ["untees", "unatis"],
    30: ["tees"], 31: ["ikattis", "iktees"], 32: ["battis", "battees"],
    33: ["taintis", "tetees"], 34: ["chauntis", "chautees"], 35: ["paintis", "paitees"],
    36: ["chhattis", "chattis"], 37: ["saintis", "saitees"], 38: ["artis", "adtees"],
    39: ["untalis", "unchaalis"], 40: ["chalis", "chaalis"], 41: ["iktalis", "iktalees"],
    42: ["bayalis", "bayalees"], 43: ["taintalis", "tetalis"], 44: ["chavalis", "chauvalis"],
    45: ["paintalis", "pentalis"], 46: ["chhiyalis", "chiyalis"], 47: ["saintalis", "sentalis"],
    48: ["adtalis", "artalis"], 49: ["unchas", "unchaas"], 50: ["pachas", "pachaas"],
    51: ["ikyavan", "ikyaavan"], 52: ["bavan", "baavan"], 53: ["tirepan", "tirpan"],
    54: ["chauvan", "chauwan"], 55: ["pachpan"], 56: ["chhappan", "chappan"],
    57: ["sattavan"], 58: ["atthavan"], 59: ["unsath", "unsaath"], 60: ["saath", "sath"],
    61: ["iksath", "iksaath"], 62: ["basath", "baasath"], 63: ["tirsath", "tiresath"],
    64: ["chausath", "chaunsath"], 65: ["painsath", "pensath"],
    66: ["chhiyasath", "chiyasath"], 67: ["sadsath", "sarsath"], 68: ["adsath", "arsath"],
    69: ["unhattar"], 70: ["sattar", "sattur"], 71: ["ikhattar"], 72: ["bahattar"],
    73: ["tihattar"], 74: ["chauhattar"], 75: ["pachhattar", "pachattar"],
    76: ["chhihattar"], 77: ["satattar", "sathattar"], 78: ["athattar"],
    79: ["unasi", "unaasi"], 80: ["assi", "assee"], 81: ["ikyasi"], 82: ["bayasi"],
    83: ["tirasi"], 84: ["chaurasi"], 85: ["pachasi"], 86: ["chhiyasi"],
    87: ["sataasi", "sattasi"], 88: ["athasi", "athaasi"], 89: ["navasi", "nawasi"],
    90: ["nabbe", "navve"], 91: ["ikyanve"], 92: ["baanve", "bannve"], 93: ["tiranve"],
    94: ["chauranve"], 95: ["pachanve"], 96: ["chhiyanve"], 97: ["sattanve"],
    98: ["atthanve"], 99: ["ninyanve", "ninyaanve"],
}
AMOUNT_WORDS = {spelling: n for n, spellings in SPELLINGS.items() for spelling in spellings}
# Words that are a number only right before a multiplier or a rupee word.
ALSO_WORDS = {"saath", "sath"}
