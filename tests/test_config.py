"""Tests for leo/config.py, using config.yaml and temporary copies of it."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from leo.config import CONFIG_PATH, PROJECT_ROOT, load_config


# The real config.yaml in the repo loads without errors.
def test_real_config_loads():
    config = load_config()
    assert config.server.port == 8000


# The primary model is the GPU-only build, with thinking turned off.
def test_primary_model_is_leo_qwen3_without_thinking():
    primary = load_config().llm.primary
    assert primary.model == "leo-qwen3"
    assert primary.think is False


# A config missing the primary model name is rejected.
def test_missing_primary_model_is_rejected(tmp_path: Path):
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    del data["llm"]["primary"]["model"]
    broken = tmp_path / "config.yaml"
    broken.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_config(broken)


# The database path is leo_data/leo.db under the project folder.
def test_db_path_resolves_under_project():
    storage = load_config().storage
    assert storage.resolved_db_path() == PROJECT_ROOT / "leo_data" / "leo.db"


# The agent step limit comes from config.yaml (default 4) and must be at least 1.
def test_agent_max_steps_is_loaded_and_checked(tmp_path: Path):
    assert load_config().agent.max_steps == 6
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    data["agent"]["max_steps"] = 0
    broken = tmp_path / "config.yaml"
    broken.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_config(broken)


# The supervisor hop limit comes from config.yaml and must be at least 1.
def test_max_hops_is_loaded_and_checked(tmp_path: Path):
    assert load_config().graph.max_hops == 8
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    data["graph"]["max_hops"] = 0
    broken = tmp_path / "config.yaml"
    broken.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_config(broken)


# The language section gives the parser's time zone (IST).
def test_language_section_loads():
    assert load_config().language.timezone == "Asia/Kolkata"


# The research section loads, and an unknown key in it is rejected.
def test_research_section_loads_and_rejects_unknown_keys(tmp_path: Path):
    research = load_config().research
    assert research.timezone == "Asia/Kolkata"
    assert research.max_redirects == 5
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    data["research"]["api_key"] = "x"
    broken = tmp_path / "config.yaml"
    broken.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_config(broken)
