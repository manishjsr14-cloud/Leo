"""M2.3 timeout probe: why did every local-model call time out in the M2.3 check?

  python -m evals.m2_3_timeout_probe REPORT_STEM
  (writes evals/reports/REPORT_STEM.md and REPORT_STEM.json)

A measuring tool only; Leo's code is not changed. Rounds alternate "without"
and "with" the e5 embedder loaded (as in the M2.3 check, in the same process
that calls Ollama); each round is a fresh Python process. Each round: unload leo-qwen3 from Ollama, record free RAM and page-file use, send one
cold request with no client time limit, and record the first-token time, the
total time and Ollama's own load_duration, then RAM and page file again and
where the model runs (GPU share from /api/ps). A last step, with the embedder
loaded, sends Leo's own warm-up (the 20 s first-token limit) to a cold model
and checks whether the model is loaded afterwards.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import psutil

from evals.git_state import git_state
from evals.m2_3_probe_report import report
from evals.machine import machine_line
from leo.config import load_config
from leo.llm.warmup import warm_up
from leo.ml.embedder import load_embedder

REPORTS = Path(__file__).resolve().parent.parent / "evals" / "reports"
ROUNDS = ["without", "with", "without", "with"]
MIB = 2**20


# Free RAM, page-file use and this process's RAM, in MiB.
def memory() -> dict:
    vm, swap = psutil.virtual_memory(), psutil.swap_memory()
    return {"available_mib": round(vm.available / MIB), "page_file_used_mib": round(swap.used / MIB),
            "page_file_total_mib": round(swap.total / MIB),
            "this_process_mib": round(psutil.Process().memory_info().rss / MIB)}


# Ollama's loaded models: name, size and the share held in VRAM.
def loaded(base: str) -> list[dict]:
    models = httpx.get(f"{base}/api/ps", timeout=30).json().get("models", [])
    return [{"name": m["name"], "size_mib": round(m["size"] / MIB),
             "gpu_share": round(m["size_vram"] / m["size"], 3) if m["size"] else None}
            for m in models]


# Unload every model and wait until Ollama reports none loaded.
def unload(base: str, model: str) -> None:
    httpx.post(f"{base}/api/generate", json={"model": model, "keep_alive": 0}, timeout=120)
    for _ in range(60):
        if not loaded(base):
            return
        time.sleep(1)


# One cold request with no client time limit: first token, total, Ollama's load time.
def cold_request(base: str, cfg) -> dict:
    body = {"model": cfg.model, "prompt": "Hi", "stream": True, "think": cfg.think,
            "options": {"num_ctx": cfg.num_ctx, "num_predict": 5}}
    start, first, last = time.perf_counter(), None, {}
    with httpx.stream("POST", f"{base}/api/generate", json=body, timeout=None) as response:
        for line in response.iter_lines():
            chunk = json.loads(line) if line else {}
            if first is None and chunk.get("response"):
                first = time.perf_counter() - start
            last = chunk or last
    return {"first_token_s": first, "total_s": time.perf_counter() - start,
            "ollama_load_s": last.get("load_duration", 0) / 1e9}


# One measured round.
def run_round(base: str, cfg, label: str) -> dict:
    unload(base, cfg.model)
    before = memory()
    result = cold_request(base, cfg)
    return {"round": label, "before": before, **result, "after": memory(),
            "loaded": loaded(base)}


# Leo's warm-up (20 s first-token limit) on a cold model, then what Ollama holds.
def warm_up_probe(base: str, config) -> dict:
    unload(base, config.llm.primary.model)
    start = time.perf_counter()
    took = warm_up(config)
    out = {"warm_up_result_s": took, "elapsed_s": time.perf_counter() - start,
           "loaded_right_after": loaded(base)}
    time.sleep(60)
    out["loaded_60_s_later"] = loaded(base)
    return out


# One round in this process: load the embedder first for "with", then measure.
# The "with" + warm-up round also runs Leo's warm-up probe.
def one_round(label: str) -> dict:
    config = load_config()
    cfg, base, embed, embedder = config.llm.primary, config.llm.primary.base_url, {}, None
    if label in ("with", "with_warm_up"):
        embed["before"] = memory()
        start = time.perf_counter()
        embedder = load_embedder(config.embedder)  # kept alive until the round ends
        embedder.embed_query("warm")
        embed["load_s"], embed["after"] = round(time.perf_counter() - start, 1), memory()
    if label == "with_warm_up":
        out = {"round": label, "embedder": embed, **warm_up_probe(base, config)}
    else:
        out = {**run_round(base, cfg, label), "embedder": embed}
    out["embedder_held"] = embedder is not None
    return out


# Run each round in a fresh Python process and collect its JSON line.
def measure() -> dict:
    cfg = load_config().llm.primary
    rounds = []
    for label in [*ROUNDS, "with_warm_up"]:
        done = subprocess.run([sys.executable, "-m", "evals.m2_3_timeout_probe", "--round", label],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              check=False, timeout=1800)
        lines = done.stdout.strip().splitlines()
        rounds.append(json.loads(lines[-1]) if done.returncode == 0 and lines
                      else {"round": label, "error": done.stderr.strip()[-500:]})
    return {"rounds": rounds, "ollama_timeouts": {"first_token_s": cfg.first_token_timeout_s,
                                                  "total_s": cfg.total_timeout_s}}


# Run the probe (or, with --round, one round) and write the report.
def main() -> None:
    if sys.argv[1] == "--round":
        print(json.dumps(one_round(sys.argv[2])))
        return
    stem, r = sys.argv[1], measure()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{stem}.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
    head = [f"# M2.3 timeout probe ({datetime.now():%Y-%m-%d %H:%M})", "", machine_line(),
            f"Commit: {git_state()}.", ""]
    (REPORTS / f"{stem}.md").write_text("\n".join(head + report(r)) + "\n", encoding="utf-8")
    print(f"wrote {stem}.md and {stem}.json")


if __name__ == "__main__":
    main()
