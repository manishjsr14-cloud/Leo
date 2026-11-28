"""The M2.4 restart check's plumbing, run in-process with a fake model (no Ollama,
no subprocess, a temporary database): both parts' events, the state check and
the report. The real check runs each part in its own process and kills part 1."""

import io
import json
import sys

import yaml

from evals import m2_4_child as child
from evals import m2_4_restart_check as check
from evals.m2_4_report import report
from leo.llm import gateway
from tests.graph_fakes import llm_result

ALL_KEYS = "B3, 1:30, 12956, HX4471, Govind, 25000"


# A fake gateway.chat: an empty plan for the supervisor, a summary line, else a reply.
def fake_chat(messages, output_model=None, force_cloud=False):
    if output_model is not None:
        parsed = output_model.model_validate({"agents": [], "task": "none"})
        return llm_result(json.dumps({"agents": [], "task": "none"}), parsed)
    if str(messages[-1]["content"]).startswith("<summary>"):
        return llm_result(f"- facts: {ALL_KEYS}")
    return llm_result(f"Noted: {ALL_KEYS}.")


# Run one part of the child in-process; return its events like run_child would.
def run_part(monkeypatch, capsys, db, variant: str, part: str) -> dict:
    monkeypatch.setattr(sys, "argv", ["m2_4_child", str(db), variant, part])
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    child.main()
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    return {"events": events, "killed": part == "1", "exit_code": 1 if part == "1" else 0}


# Both variants end to end with the fake model: the summary variant passes the
# rule, the state after the restart is the state before it, and the report renders.
def test_restart_check_plumbing(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(gateway, "chat", fake_chat)
    monkeypatch.setattr(child, "load_model", lambda config: None)
    data = yaml.safe_load(child.SET.read_text(encoding="utf-8"))
    runs = {}
    for variant in check.VARIANTS:
        db = tmp_path / f"{variant}.db"
        first = run_part(monkeypatch, capsys, db, variant, "1")
        second = run_part(monkeypatch, capsys, db, variant, "2")
        runs[variant] = {"db": str(db), **check.assemble(first, second, data)}
        runs[variant]["parts"] = check.judge(runs[variant], data)
    summary = runs["summary"]
    assert summary["after_restart"] == summary["before_kill"]
    assert summary["before_kill"]["summary"].startswith("- facts")
    assert len(summary["before_kill"]["messages"]) == 8  # P17-P20
    assert [ok for _, ok in summary["parts"]] == [True, True, True]
    assert len(runs["no_summary"]["before_kill"]["messages"]) == 40
    assert not runs["no_summary"]["parts"][2][1]  # no summary without the summary node
    calls = [c["node"] for t in summary["turns"].values() for c in t["calls"]]
    assert "summary" in calls
    result = {"machine": "Machine: test", "commit": "abc", "set": child.SET.as_posix(),
              "now": data["now"], "model": "fake", "runs": runs,
              "conversation": {"summarize_after": 12, "keep_messages": 6}}
    text = "\n".join(report(result, data))
    assert "**Result: PASSED**" in text and "| R5 | B3 | yes | recent |" in text
