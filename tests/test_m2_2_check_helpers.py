"""Tests for evals/m2_2_check_helpers.py: cosine, pairs from the file and rule B."""

import math
from pathlib import Path

from evals.m2_2_check_helpers import (
    cosine,
    load_pairs,
    near_pairs,
    report,
    rule_b,
    sentence_texts,
)

PAIRS = Path(__file__).resolve().parent.parent / "evals/scenarios/m2_2_embedder_pairs.yaml"


# Cosine: same direction 1, opposite -1, at right angles 0, length does not matter.
def test_cosine():
    assert math.isclose(cosine([1, 0], [3, 0]), 1.0)
    assert math.isclose(cosine([1, 0], [-2, 0]), -1.0)
    assert math.isclose(cosine([1, 0], [0, 5]), 0.0)


# Every group gives three near pairs and every name has a text.
def test_near_pairs_from_file():
    data = load_pairs(PAIRS)
    texts = sentence_texts(data)
    pairs = near_pairs(data)
    assert len(pairs) == 3 * len(data["near_groups"])
    assert all(a in texts and b in texts for a, b in pairs)
    assert ("g03.en", "g03.hinglish") in pairs


# Rule B passes when every near pair beats every far pair of the same sentence.
def test_rule_b_passes():
    near = {("x.en", "x.hi"): 0.9, ("x.en", "x.hinglish"): 0.85}
    far = {("x.en", "y.en"): 0.84}
    row = rule_b(["x.en"], near, far)[0]
    assert row == {"sentence": "x.en", "lowest_near": 0.85, "highest_far": 0.84, "ok": True}


# Rule B fails when one far pair beats the weakest near pair; a tie also fails.
def test_rule_b_fails_on_overlap_and_tie():
    near = {("x.en", "x.hi"): 0.9, ("x.en", "x.hinglish"): 0.8}
    assert rule_b(["x.en"], near, {("x.en", "y.en"): 0.81})[0]["ok"] is False
    assert rule_b(["x.en"], near, {("x.en", "y.en"): 0.8})[0]["ok"] is False


# Far pairs of other sentences do not count against this one.
def test_rule_b_ignores_other_sentences():
    near = {("x.en", "x.hi"): 0.7}
    far = {("z.en", "y.en"): 0.99}
    assert rule_b(["x.en"], near, far)[0]["ok"] is True


# The report says FAILED and names the failing sentence, and shows a recorded
# pair next to the weakest near pair of its sentence.
def test_report_names_failures_and_recorded_pairs():
    r = {"model": "m", "device": "cpu", "dimension": 384, "cache_dir": "models/hf_cache",
         "was_cached": True, "cache_mib": 1.0, "offline_reload": "offline load ok",
         "load_s": 1.0, "first_embed_ms": 1.0, "torch_threads": 4,
         "timing": {"runs": 20, "median_ms": 1.0, "min_ms": 1.0, "max_ms": 2.0},
         "rss_start_mib": 100.0, "rss_loaded_mib": 300.0, "rss_end_mib": 310.0,
         "peak_mib": None, "passed": False,
         "near": [{"a": "x.en", "b": "x.hi", "similarity": 0.8}],
         "far": [{"a": "x.en", "b": "y.en", "similarity": 0.9, "hard": True}],
         "recorded": [{"a": "x.en", "b_text": "parso", "similarity": 0.95}],
         "rule_b": [{"sentence": "x.en", "lowest_near": 0.8, "highest_far": 0.9, "ok": False}]}
    text = "\n".join(report(r, ["# title"]))
    assert "FAILED under rule B (0/1 sentences pass). Failing: x.en." in text
    assert "| x.en | parso | 0.950 | lowest near pair of x.en: 0.800 |" in text
    assert "(+200)" in text
