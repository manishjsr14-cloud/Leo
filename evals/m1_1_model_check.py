"""M1.1 real-model check. Writes measured output to a report in evals/reports/.

  python -m evals.m1_1_model_check local REPORT   # GPU, thinking, cold/warm, check set
  python -m evals.m1_1_model_check groq REPORT    # one real Groq call (force_cloud)

Uses the real local model and Groq, but no tools, calendar or personal data.
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml
from openai import OpenAI
from pydantic import ValidationError

from evals.m1_1_schemas import SCHEMAS
from evals.machine import machine_line
from leo.config import load_config
from leo.llm import clients, gateway

ROOT = Path(__file__).resolve().parent.parent
CHECK_SET = ROOT / "evals" / "scenarios" / "m1_1_schema_check.yaml"
ONE_LINE = "Reply with one short sentence: what is the capital of India?"


# Run a command and return its output text (stdout and stderr).
def run(cmd: list[str]) -> str:
    done = subprocess.run(cmd, check=False, capture_output=True, text=True, encoding="utf-8")
    return (done.stdout + done.stderr).strip()


# Time one streamed request with a long timeout, so a slow cold start is measured
# instead of being cut off by the gateway's 20 s limit.
def timed_reply(messages: list[dict], output_model=None) -> clients.StreamResult:
    cfg = load_config().llm.primary
    client = OpenAI(base_url=cfg.base_url.rstrip("/") + "/v1", api_key="ollama",
                    timeout=180, max_retries=0)
    request = clients.ollama_request(cfg, messages, output_model)
    return clients.run_stream(client, request, total_timeout_s=180)


# Unload the model and wait until "ollama ps" no longer lists it.
def unload(model: str) -> None:
    run(["ollama", "stop", model])
    for _ in range(30):
        if model not in run(["ollama", "ps"]):
            return
        time.sleep(1)


# Cold and warm time to first token, then the gateway thinking check.
def speed_section(model: str) -> list[str]:
    msgs = [{"role": "user", "content": ONE_LINE}]
    unload(model)
    lines = [(f"## Time to first token\nAfter `ollama stop {model}`, ps shows: "
             f"{'not loaded' if model not in run(['ollama', 'ps']) else 'STILL LOADED'}")]
    for label in ("cold", "warm"):
        r = timed_reply(msgs)
        lines.append(f"- {label}: first_token_s={r.first_token_s:.2f} total_s={r.total_s:.2f} "
                     f"completion_tokens={r.completion_tokens}")
    result = gateway.chat(msgs)
    lines += ["", f"## Thinking check (gateway.chat, prompt: '{ONE_LINE}')",
              (f"- provider={result.provider} model={result.model} "
              f"fallback_reason={result.fallback_reason}"),
              (f"- completion_tokens={result.completion_tokens} total_s={result.total_s:.2f} "
              f"first_token_s={result.first_token_s:.2f}"),
              f"- reasoning or <think> text arrived before stripping: {result.thinking_seen}",
              f"- reply: {result.text!r}"]
    return lines


# Run the fixed check set and count replies that pass the schema.
def check_set_section() -> list[str]:
    data = yaml.safe_load(CHECK_SET.read_text(encoding="utf-8"))
    valid = matched = 0
    rows = []
    for item in data["prompts"]:
        schema = SCHEMAS[item["schema"]]
        msgs = [{"role": "system", "content": data["system_prompts"][item["schema"]]},
                {"role": "user", "content": item["text"]}]
        r = timed_reply(msgs, schema)
        try:
            fields = schema.model_validate_json(r.text).model_dump(mode="json")
            ok = True
        except ValidationError:
            fields, ok = {}, False
        hit = ok and all(fields.get(k) == v for k, v in item["expected"].items())
        valid += ok
        matched += hit
        rows.append(f"| {item['id']} | {item['schema']} | {ok} | {hit} | "
                    f"{r.completion_tokens} | {r.total_s:.2f} | `{r.text}` |")
    return [f"## Check set ({CHECK_SET.name}, version {data['version']})",
            (f"Valid for schema: {valid}/{len(rows)}. Matched expected values: "
            f"{matched}/{len(rows)}."), "",
            "| id | schema | valid | matched expected | completion_tokens | total_s | reply |",
            "|---|---|---|---|---|---|---|", *rows]


# GPU placement and memory, read while the model is loaded.
def gpu_section() -> list[str]:
    smi = run(["nvidia-smi", "--query-gpu=name,memory.used,memory.total",
               "--format=csv,noheader"])
    return ["## GPU", "```", run(["ollama", "ps"]), "```", f"nvidia-smi: {smi}"]


# One real Groq call with force_cloud=True; failures are reported, not hidden.
def groq_section() -> list[str]:
    lines = [f"## Real Groq call (force_cloud=True, prompt: '{ONE_LINE}')"]
    try:
        r = gateway.chat([{"role": "user", "content": ONE_LINE}], force_cloud=True)
    except gateway.LLMUnavailable as error:
        return lines + [f"- FAILED: {error}"]
    return lines + [f"- provider={r.provider} model={r.model}",
                    f"- prompt_tokens={r.prompt_tokens} completion_tokens={r.completion_tokens}",
                    f"- first_token_s={r.first_token_s:.2f} total_s={r.total_s:.2f}",
                    f"- reply: {r.text!r}"]


# Write the chosen part to the report file (local creates it, groq appends).
def main() -> None:
    part, report = sys.argv[1], Path(sys.argv[2])
    model = load_config().llm.primary.model
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    if part == "local":
        header = [f"# M1.1 model check — {stamp}", machine_line(), (f"Model: {model}. "
                  f"{run(['ollama', '--version'])}."), ""]
        lines = header + speed_section(model) + [""] + gpu_section() + [""] + check_set_section()
        report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        with report.open("a", encoding="utf-8") as f:
            f.write("\n" + "\n".join([f"<!-- run {stamp}; {machine_line()} -->",
                                       *groq_section()]) + "\n")
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
