"""Tests for the M1 cleanup report readers: the temperature comparison and the
done check. Reports here are small dicts like run_eval's .json; nothing runs."""

from evals import m1_cleanup_done_check as done
from evals import m1_cleanup_temperature_compare as temps
from evals.eval_metrics import compute


# One turn record like run_eval's, passing unless `fail` says which check fails.
def turn(key: str, fail: str = "", known: bool = False, reply: str = "Done.") -> dict:
    t = {"key": key, "lang": "en", "reply": reply, "steps": [], "plan": [],
         "routing_ok": True, "tools_ok": fail != "tools", "lang_ok": fail != "lang",
         "lang_why": "", "tool_fails": ["missing call x"] if fail == "tools" else [],
         "reply_fails": [], "known": known, "llm_calls": 2, "turn_s": 5.0,
         "refused": [], "fallback_calls": 0}
    passed = not fail
    t["verdict"] = ("fixed" if passed else "known_failing") if known else (
        "pass" if passed else "fail")
    return t


# A report from turns, at a temperature.
def report(turns: list[dict], temp: str = "0.7", machine: str = "Machine: laptop (GPU: x)"):
    return {"machine": machine, "commit": "abc", "dirty": False, "turns": turns,
            "sampling": f"Sampling: Leo's requests set temperature {temp} (config.yaml)",
            "metrics": compute(turns)}


def test_done_rule_uses_v2_on_both_sides():
    base = done.with_v2_report(report([turn("f:a"), turn("f:g")]))
    # f:g fails only v1's language check; its English reply passes v2.
    run = done.with_v2_report(report([turn("f:a"), turn("f:g", fail="lang")]))
    passed, lines = done.check(run, base)
    assert passed
    assert "- newly failing, scorer v1 (reported alongside): 1" in lines


def test_done_rule_fails_on_a_new_tool_failure_or_another_machine():
    base = done.with_v2_report(report([turn("f:a")]))
    assert not done.check(done.with_v2_report(report([turn("f:a", fail="tools")])), base)[0]
    desktop = report([turn("f:a")], machine="Machine: desktop (GPU: y)")
    assert not done.check(done.with_v2_report(desktop), base)[0]


def test_temperature_report_counts_noise_flips_and_temperature_flips():
    base = ("base", temps.with_v2_report(report([turn("f:a"), turn("f:b")])))
    runs = [("r1", report([turn("f:a"), turn("f:b")], "0.7")),
            ("r2", report([turn("f:a"), turn("f:b", fail="tools")], "0.7")),
            ("r3", report([turn("f:a"), turn("f:b")], "0.3")),
            ("r4", report([turn("f:a"), turn("f:b")], "0.3"))]
    text = "\n".join(temps.report(base, [(n, temps.with_v2_report(r)) for n, r in runs]))
    assert "- 0.7: r1 -> r2, verdict_v2: 1" in text
    assert "- 0.3: r3 -> r4, verdict_v2: 0" in text
    assert "- r2 vs r3: 1" in text
    assert "- r2: v1 1, v2 (both sides) 1" in text


def test_temperature_report_lists_commits_and_tree_state(monkeypatch):
    import subprocess
    monkeypatch.setattr(temps.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a, 0, stdout="evals/reports/x.md\n", stderr=""))
    one = report([turn("f:a")], "0.7")
    two = {**report([turn("f:a")], "0.3"), "commit": "def", "dirty": True}
    lines = temps.commits([("r1", one), ("r2", two)])
    assert lines == ["- r1: commit abc (clean)",
                     "- r2: commit def (recorded 'uncommitted changes present')",
                     "- files changed between abc and def: evals/reports/x.md"]
