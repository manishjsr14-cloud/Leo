"""Leo never installs Langfuse's automatic integrations (the OpenAI wrapper,
the LangChain/LangGraph callback handler, OpenTelemetry instrumentors): they
record full prompts and replies whatever tracing.include_text says.
"""

import subprocess
import sys

from leo.config import PROJECT_ROOT


# Importing and running Leo with the real Langfuse client installs no automatic
# integration (OpenAI wrapper, LangChain callback, OpenTelemetry instrumentors).
# Runs in a fresh Python; the client points at a closed local port, so tracing
# turns itself off with one warning and nothing leaves the machine.
def test_no_automatic_integrations_are_installed():
    code = """
import logging, sys
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
import openai
original_create = openai.resources.chat.completions.Completions.create
from leo import cli
from leo.config import Secrets, load_config
from leo.graph.builder import build_graph
from leo.ops.tracing_setup import setup_tracing
from tests.graph_fakes import FakeChat
keys = Secrets(_env_file=None, langfuse_public_key="pk-test", langfuse_secret_key="sk-test",
               langfuse_host="http://127.0.0.1:9")
print("on", setup_tracing(load_config(), keys))
print("reply", cli.run_turn(build_graph(FakeChat("hi")), [], "hello", False)[0].content)
bad = [m for m in sys.modules
       if m.startswith(("langfuse.openai", "langfuse.langchain", "opentelemetry.instrumentation"))]
print("integrations", bad)
create = openai.resources.chat.completions.Completions.create
print("openai unchanged", create is original_create)
"""
    out = subprocess.run([sys.executable, "-c", code], cwd=PROJECT_ROOT, capture_output=True,
                         text=True, timeout=60, check=True)
    assert "on False" in out.stdout and "reply hi" in out.stdout
    assert "integrations []" in out.stdout
    assert "openai unchanged True" in out.stdout  # not patched by langfuse.openai
    assert out.stderr.count("WARNING leo.ops") == 1


# No file in leo/ refers to an automatic integration.
def test_source_uses_no_automatic_integration():
    banned = ["langfuse.openai", "langfuse.langchain", "CallbackHandler", "@observe",
              "opentelemetry.instrumentation"]
    for path in (PROJECT_ROOT / "leo").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for word in banned:
            assert word not in source, f"{path.name} uses {word}"
