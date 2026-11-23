"""Tests for evals/eval_metrics.py: per-language rates and number summaries."""

from evals.eval_metrics import compute, nearest_rank, summary, table


# A scored turn record with the fields compute() reads.
def rec(lang, ok=True, tools=True, calls=2, seconds=5.0, refused=()):
    return {"lang": lang, "routing_ok": ok, "tools_ok": tools, "reply_ok": ok, "lang_ok": ok,
            "clock_ok": True, "json_ok": True, "invented_ok": True, "passed": ok,
            "llm_calls": calls, "turn_s": seconds, "refused": list(refused),
            "fallback_calls": 0}


# Nearest rank on fixed numbers.
def test_nearest_rank():
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert nearest_rank(values, 0.5) == 5
    assert nearest_rank(values, 0.95) == 10
    assert nearest_rank([7], 0.95) == 7


# avg, max and total; an empty list gives None.
def test_summary():
    s = summary([2, 3, 7])
    assert (s["avg"], s["max"], s["total"], s["n"]) == (4, 7, 12, 3)
    assert summary([]) is None


# Rates split by language; a None check is not counted.
def test_compute_splits_by_language():
    records = [rec("hinglish"), rec("hinglish", ok=False), rec("en", tools=None)]
    m = compute(records)
    assert m["rates"]["routing accuracy"] == {"all": [2, 3], "hinglish": [1, 2], "en": [1, 1]}
    assert m["rates"]["tool-call accuracy"]["en"] == [0, 0]
    assert m["numbers"]["LLM calls per turn"]["all"]["avg"] == 2


# Refused calls per turn are counted from the lists.
def test_refused_counted():
    m = compute([rec("en", refused=["a (needs approval)", "b (error: x)"]), rec("en")])
    assert m["numbers"]["refused calls per turn"]["en"]["total"] == 2


# A language with no turns shows "-" in the table.
def test_table_with_empty_language():
    lines = table(compute([rec("hinglish")]))
    routing = next(line for line in lines if line.startswith("| routing accuracy"))
    assert routing.endswith("| - |")
