"""M2.2 real check: the e5 embedder on the frozen check set. Writes a report.

  python -m evals.m2_2_embedder_check REPORT_STEM
  (writes evals/reports/REPORT_STEM.md and REPORT_STEM.json)

Measures, on this machine: every pair's similarity and the rule B result
(evals/scenarios/m2_2_embedder_pairs.yaml), load time, time to embed one
message, extra RAM of this process, and a reload in a fresh process with
Hugging Face set offline. Uses no personal data and no tools.
"""

import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

from evals.git_state import git_state
from evals.m2_2_check_helpers import (
    cosine,
    load_pairs,
    near_pairs,
    report,
    rule_b,
    sentence_texts,
)
from evals.machine import machine_line
from leo.config import load_config
from leo.ml.embedder import load_embedder

ROOT = Path(__file__).resolve().parent.parent
PAIRS = ROOT / "evals" / "scenarios" / "m2_2_embedder_pairs.yaml"
REPORTS = ROOT / "evals" / "reports"
TIMED_RUNS = 20
OFFLINE_LOAD = ("from leo.config import load_config; from leo.ml.embedder import load_model; "
                "load_model(load_config().embedder); print('offline load ok')")


# This process's resident memory in MiB.
def rss_mib() -> float:
    return psutil.Process().memory_info().rss / 2**20


# Size in MiB of everything under a folder (the model cache).
def folder_mib(path: Path) -> float:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 2**20


# Load the model again in a fresh Python with Hugging Face offline; return its last line.
def offline_reload() -> str:
    env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    done = subprocess.run([sys.executable, "-c", OFFLINE_LOAD], check=False, cwd=ROOT,
                          env=env,
                          capture_output=True, text=True, timeout=600)
    if done.returncode == 0:
        return done.stdout.strip().splitlines()[-1]
    return f"FAILED (exit {done.returncode}): {done.stderr.strip().splitlines()[-1]}"


# Milliseconds to embed one message, straight through the model (the reuse cache
# would otherwise answer from memory): one warm-up, then TIMED_RUNS timed runs.
def time_one_message(emb, text: str) -> dict:
    batch = [emb.cfg.query_prefix + text]
    emb.model.encode(batch, normalize_embeddings=True)
    times = []
    for _ in range(TIMED_RUNS):
        start = time.perf_counter()
        emb.model.encode(batch, normalize_embeddings=True)
        times.append((time.perf_counter() - start) * 1000)
    return {"runs": TIMED_RUNS, "median_ms": statistics.median(times),
            "min_ms": min(times), "max_ms": max(times)}


# Run every measurement and return the results as one dict.
def measure() -> dict:
    cfg = load_config().embedder
    data = load_pairs(PAIRS)
    texts = sentence_texts(data)
    cache = cfg.resolved_cache_dir()
    was_cached = cache.exists() and any(cache.iterdir())
    rss_start = rss_mib()
    start = time.perf_counter()
    emb = load_embedder(cfg)
    load_s = time.perf_counter() - start
    rss_loaded = rss_mib()
    start = time.perf_counter()
    emb.embed_query(texts["g01.en"])
    first_ms = (time.perf_counter() - start) * 1000
    vec = {name: emb.embed_query(text) for name, text in texts.items()}
    near = {p: cosine(vec[p[0]], vec[p[1]]) for p in near_pairs(data)}
    far = {(p["a"], p["b"]): cosine(vec[p["a"]], vec[p["b"]]) for p in data["far_pairs"]}
    recorded = [{"a": p["a"], "b_text": p["b_text"], "why": p["why"],
                 "similarity": cosine(vec[p["a"]], emb.embed_query(p["b_text"]))}
                for p in data["recorded_pairs"]]
    timing = time_one_message(emb, texts["g03.hinglish"])
    import torch  # already loaded by the model; only read its thread count
    info = psutil.Process().memory_info()
    peak = getattr(info, "peak_wset", None)
    rows = rule_b(list(texts), near, far)
    hard = {(p["a"], p["b"]) for p in data["far_pairs"] if p.get("hard")}
    return {"model": cfg.model, "device": str(emb.model.device), "dimension": len(vec["g01.en"]),
            "cache_dir": cfg.cache_dir.as_posix(), "was_cached": was_cached,
            "cache_mib": folder_mib(cache), "load_s": load_s, "first_embed_ms": first_ms,
            "timing": timing, "torch_threads": torch.get_num_threads(),
            "rss_start_mib": rss_start, "rss_loaded_mib": rss_loaded,
            "rss_end_mib": info.rss / 2**20, "peak_mib": peak / 2**20 if peak else None,
            "offline_reload": offline_reload(),
            "near": [{"a": a, "b": b, "similarity": s} for (a, b), s in near.items()],
            "far": [{"a": a, "b": b, "similarity": s, "hard": (a, b) in hard}
                    for (a, b), s in far.items()],
            "recorded": recorded, "rule_b": rows, "passed": all(r["ok"] for r in rows)}


# Run the check and write REPORT_STEM.md and REPORT_STEM.json.
def main() -> None:
    stem = sys.argv[1]
    results = measure()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{stem}.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                          encoding="utf-8")
    header = [f"# M2.2 embedder check ({datetime.now():%Y-%m-%d %H:%M})", "",
              machine_line(), f"Commit: {git_state()}.", ""]
    text = "\n".join(report(results, header)) + "\n"
    (REPORTS / f"{stem}.md").write_text(text, encoding="utf-8")
    print(f"{'PASSED' if results['passed'] else 'FAILED'}; wrote {stem}.md and {stem}.json")


if __name__ == "__main__":
    main()
