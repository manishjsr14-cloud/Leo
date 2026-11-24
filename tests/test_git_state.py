"""Tests for evals/git_state.py: report files under evals/reports/ never make a
run look dirty; any other change does. No real git command is run."""

import subprocess

from evals import git_state as gs


# git_state with fake git output: HEAD "abc1234" and this `git status --porcelain`.
def state_with(monkeypatch, porcelain: str) -> str:
    def fake_run(args, **kwargs):
        out = "abc1234\n" if args[1] == "rev-parse" else porcelain
        return subprocess.CompletedProcess(args, 0, stdout=out, stderr="")
    monkeypatch.setattr(gs.subprocess, "run", fake_run)
    return gs.git_state()


def test_untracked_report_file_leaves_the_run_clean(monkeypatch):
    porcelain = "?? evals/reports/m1_cleanup_eval_2026-11-24_t07_run1.md\n"
    assert state_with(monkeypatch, porcelain) == "abc1234"


def test_edited_file_outside_reports_marks_the_run_dirty(monkeypatch):
    porcelain = " M leo/cli.py\n?? evals/reports/x.md\n"
    assert state_with(monkeypatch, porcelain) == "abc1234 (uncommitted changes present)"


def test_clean_tree_is_clean(monkeypatch):
    assert state_with(monkeypatch, "") == "abc1234"


def test_outside_reports_reads_renames_and_untracked_files():
    porcelain = ("R  evals/old.py -> evals/reports/old.py\n"
                 "R  evals/reports/a.md -> docs/a.md\n"
                 "?? tests/new_test.py\n M evals/reports/r.json\n")
    assert gs.outside_reports(porcelain) == ["evals/old.py", "docs/a.md", "tests/new_test.py"]
