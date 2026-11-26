"""Report lines for the M2.3 timeout probe (evals/m2_3_timeout_probe.py)."""


# Seconds with one decimal, or "-".
def sec(value) -> str:
    return "-" if value is None else f"{value:.1f}"


# The report lines.
def report(r: dict) -> list[str]:
    lines = [("| round | free RAM before (MiB) | page file used before | embedder load s | "
             "free RAM after | page file used after | Ollama load s | first token s | total s | "
             "GPU share |"), "|---|---|---|---|---|---|---|---|---|---|"]
    for x in r["rounds"]:
        if "error" in x or x["round"] == "with_warm_up":
            continue
        e = x["embedder"]
        b = e.get("before", x["before"])
        gpu = ", ".join(str(m["gpu_share"]) for m in x["loaded"]) or "-"
        lines.append(f"| {x['round']} | {b['available_mib']} | {b['page_file_used_mib']} | "
                     f"{e.get('load_s', '-')} | {x['after']['available_mib']} | "
                     f"{x['after']['page_file_used_mib']} | {sec(x['ollama_load_s'])} | "
                     f"{sec(x['first_token_s'])} | {sec(x['total_s'])} | {gpu} |")
    w = next((x for x in r["rounds"] if x["round"] == "with_warm_up"), {})
    errors = [x for x in r["rounds"] if "error" in x]
    lines += ["", ("Free RAM before: for \"with\" rounds, before the embedder was loaded; the "
              "embedder's RAM shows in the \"after\" columns of that round."),
              (f"Leo's time limits: first token {r['ollama_timeouts']['first_token_s']} s, total "
              f"{r['ollama_timeouts']['total_s']} s."), "",
              ("Leo's warm-up on a cold model, embedder loaded: "
              f"result {w.get('warm_up_result_s')}, elapsed {sec(w.get('elapsed_s'))} s; "
              f"loaded right after: {w.get('loaded_right_after')}; 60 s later: "
              f"{w.get('loaded_60_s_later')}."),
              f"Rounds that failed: {[(x['round'], x['error']) for x in errors] or 'none'}."]
    return lines
