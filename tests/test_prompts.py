"""Tests for the versioned prompt files (prompts/*.yaml, leo/llm/prompts.py)."""

from pathlib import Path

import pytest

from leo.language.normalize import language_tag
from leo.llm.prompts import PROMPTS_DIR, Prompt, load_prompt

AGENT_PROMPTS = {"calendar": ["tools", "today", "times", "task"],
                 "productivity": ["tools", "task"],
                 "research": ["tools", "today", "task"]}


def test_every_prompt_file_loads_with_a_whole_number_version():
    names = sorted(p.stem for p in PROMPTS_DIR.glob("*.yaml"))
    assert names == ["calendar", "memory", "productivity", "replies", "research", "responder",
                     "supervisor"]
    for name in names:
        prompt = load_prompt(name)
        assert isinstance(prompt.version, int) and prompt.version >= 1
        assert prompt.tag == f"{name}@{prompt.version}"


@pytest.mark.parametrize("name", sorted(AGENT_PROMPTS))
def test_agent_prompts_fill_in_and_have_a_hinglish_example(name):
    prompt = load_prompt(name)
    text = prompt.render(**{key: f"<{key}>" for key in AGENT_PROMPTS[name]})
    assert all(f"<{key}>" in text for key in AGENT_PROMPTS[name])
    assert any(language_tag(e.split("->")[0], 0.2) == "hinglish" for e in prompt.examples)


def test_supervisor_and_responder_have_hinglish_examples():
    agents = load_prompt("supervisor").extra("agents")
    examples = [e for agent in agents.values() for e in agent["examples"]]
    assert all(language_tag(e, 0.2) == "hinglish" for e in examples)
    responder = load_prompt("responder")
    assert responder.examples
    assert any(language_tag(e.split("->")[1], 0.2) == "en" for e in responder.examples)


def test_reply_templates_cover_both_languages():
    replies = load_prompt("replies")
    en, hinglish = replies.extra("en"), replies.extra("hinglish")
    assert set(en) == set(hinglish)
    assert "assumed" in en


def test_examples_are_added_unformatted():
    prompt = Prompt(name="x", version=2, system="Task: {task}", examples=['a -> {"b": 1}'])
    assert prompt.render(task="t") == 'Task: t\nExamples:\n- a -> {"b": 1}'


def test_name_must_match_the_file(tmp_path: Path):
    (tmp_path / "x.yaml").write_text("name: y\nversion: 1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_prompt("x", tmp_path)
