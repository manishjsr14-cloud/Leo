"""Scoring and report lines for the M2.2 embedder check (no model needed here).

The check set is evals/scenarios/m2_2_embedder_pairs.yaml. Sentences are named
"<group id>.<language>". Pass rule B (fixed in that file): for every group
sentence, each near pair containing it scores higher than each far pair
containing it. Recorded (kal/parso) pairs are shown but never scored.
"""

from pathlib import Path

import yaml

LANGS = ("en", "hinglish", "hi")


# Read the check set file.
def load_pairs(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# Map every sentence name ("g03.hi") to its text.
def sentence_texts(data: dict) -> dict[str, str]:
    return {f"{g['id']}.{lang}": g[lang] for g in data["near_groups"] for lang in LANGS}


# The three near pairs of every group, as (name a, name b).
def near_pairs(data: dict) -> list[tuple[str, str]]:
    pairs = []
    for g in data["near_groups"]:
        a, b, c = (f"{g['id']}.{lang}" for lang in LANGS)
        pairs += [(a, b), (a, c), (b, c)]
    return pairs


# Cosine similarity of two vectors (the embedder's vectors are already length 1,
# but dividing by the lengths keeps this correct for any vectors).
def cosine(u, v) -> float:
    dot = sum(x * y for x, y in zip(u, v, strict=True))
    nu = sum(x * x for x in u) ** 0.5
    nv = sum(y * y for y in v) ** 0.5
    return dot / (nu * nv)


# Rule B per sentence. `near` and `far` map (a, b) -> similarity.
# Returns one row per sentence: lowest near, highest far, and whether it passed.
def rule_b(names: list[str], near: dict, far: dict) -> list[dict]:
    rows = []
    for name in names:
        near_sims = [s for pair, s in near.items() if name in pair]
        far_sims = [s for pair, s in far.items() if name in pair]
        lowest, highest = min(near_sims), max(far_sims, default=None)
        ok = highest is None or lowest > highest
        rows.append({"sentence": name, "lowest_near": lowest, "highest_far": highest, "ok": ok})
    return rows


# Three decimals for a similarity, or "-" when there is none.
def num(value) -> str:
    return "-" if value is None else f"{value:.3f}"


# Markdown table lines for a list of pairs with their similarity.
def pair_table(title: str, rows: list[tuple[str, str, float, str]]) -> list[str]:
    lines = [f"## {title}", "", "| a | b | similarity | note |", "|---|---|---|---|"]
    lines += [f"| {a} | {b} | {num(s)} | {note} |" for a, b, s, note in rows]
    return lines + [""]


# Markdown table lines for the rule B result of every sentence.
def rule_table(rows: list[dict]) -> list[str]:
    lines = ["## Rule B per sentence", "",
             "| sentence | lowest near | highest far | result |", "|---|---|---|---|"]
    lines += [f"| {r['sentence']} | {num(r['lowest_near'])} | {num(r['highest_far'])} | "
              f"{'pass' if r['ok'] else 'FAIL'} |" for r in rows]
    return lines + [""]


# The summary bullet lines: where the model lives, speed and RAM.
def summary_lines(r: dict) -> list[str]:
    t = r["timing"]
    peak = "-" if r["peak_mib"] is None else f"{r['peak_mib']:.0f}"
    loaded = r["rss_loaded_mib"] - r["rss_start_mib"]
    end = r["rss_end_mib"] - r["rss_start_mib"]
    cached = "yes" if r["was_cached"] else "no"
    return [
        f"- Model: {r['model']}, device {r['device']}, {r['dimension']} dimensions",
        (f"- Cache: {r['cache_dir']} (project folder), {r['cache_mib']:.0f} MiB on disk; "
         f"already cached before this run: {cached}"),
        f"- Reload in a fresh process with HF_HUB_OFFLINE=1: {r['offline_reload']}",
        (f"- Load time: {r['load_s']:.1f} s; first message after load: "
         f"{r['first_embed_ms']:.0f} ms"),
        (f"- One message (median of {t['runs']} after a warm-up): {t['median_ms']:.1f} ms "
         f"(min {t['min_ms']:.1f}, max {t['max_ms']:.1f}); torch threads {r['torch_threads']}"),
        (f"- RAM of this process: {r['rss_start_mib']:.0f} MiB before loading, "
         f"{r['rss_loaded_mib']:.0f} after loading (+{loaded:.0f}), {r['rss_end_mib']:.0f} "
         f"after all embeddings (+{end:.0f}); peak working set {peak} MiB"),
        ""]


# The whole Markdown report: `header` (title, machine, commit), result, tables.
def report(r: dict, header: list[str]) -> list[str]:
    lowest = {row["sentence"]: row["lowest_near"] for row in r["rule_b"]}
    failed = [row["sentence"] for row in r["rule_b"] if not row["ok"]]
    total = len(r["rule_b"])
    result = (f"Result: {'PASSED' if r['passed'] else 'FAILED'} under rule B "
              f"({total - len(failed)}/{total} sentences pass).")
    if failed:
        result += f" Failing: {', '.join(failed)}."
    lines = header + [result, ""] + summary_lines(r)
    lines += pair_table("Near pairs (same sentence)",
                        [(p["a"], p["b"], p["similarity"], "") for p in r["near"]])
    lines += pair_table("Far pairs (different meaning, scored)",
                        [(p["a"], p["b"], p["similarity"], "hard" if p["hard"] else "")
                         for p in r["far"]])
    lines += pair_table("Recorded, not scored: kal vs parso",
                        [(p["a"], p["b_text"], p["similarity"],
                          f"lowest near pair of {p['a']}: {num(lowest[p['a']])}")
                         for p in r["recorded"]])
    return lines + rule_table(r["rule_b"])
