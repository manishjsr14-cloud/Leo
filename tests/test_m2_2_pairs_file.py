"""Shape checks for the frozen M2.2 embedder check set (no model is loaded here)."""

import re
from pathlib import Path

import yaml

PAIRS = Path(__file__).resolve().parent.parent / "evals/scenarios/m2_2_embedder_pairs.yaml"
LANGS = ("en", "hinglish", "hi")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


# Load the check set once per test.
def load() -> dict:
    with PAIRS.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# All "<group id>.<language>" names a pair may point at.
def sentence_names(data: dict) -> set[str]:
    return {f"{g['id']}.{lang}" for g in data["near_groups"] for lang in LANGS}


# Every near group has all three versions, and only the hi one is Devanagari.
def test_near_groups_have_three_versions():
    data = load()
    assert len(data["near_groups"]) >= 10
    for g in data["near_groups"]:
        assert all(g[lang].strip() for lang in LANGS), g["id"]
        assert DEVANAGARI.search(g["hi"]), g["id"]
        assert not DEVANAGARI.search(g["en"]) and not DEVANAGARI.search(g["hinglish"])


# Far pairs name real sentences, from different groups, each with a reason,
# and every group sentence is in at least one far pair (so rule B tests it).
def test_far_pairs_cover_every_sentence():
    data = load()
    names = sentence_names(data)
    used = set()
    for p in data["far_pairs"]:
        assert p["a"] in names and p["b"] in names, p
        assert p["a"].split(".")[0] != p["b"].split(".")[0], p
        assert p["why"].strip()
        used |= {p["a"], p["b"]}
    assert used == names


# At least 3 kal/parso pairs are recorded, each anchored on a group sentence.
def test_kal_parso_pairs_are_recorded():
    data = load()
    names = sentence_names(data)
    recorded = data["recorded_pairs"]
    assert len(recorded) >= 3
    for p in recorded:
        assert p["a"] in names and p["b_text"].strip() and p["why"].strip()
    assert sum("parso" in p["b_text"].lower() or "परसों" in p["b_text"] for p in recorded) >= 3


# The pass rule and the prefix are written into the file.
def test_rule_and_prefix_are_fixed():
    data = load()
    assert data["pass_rule"] == "B"
    assert data["prefix"] == "query: "
