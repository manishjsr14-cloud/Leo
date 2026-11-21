"""The responder node: turns the conversation and agent results into one reply.

The responder only sees results from tool calls that succeeded, written out
by code as plain facts (leo/graph/result_words.py): no raw JSON, so the model
cannot echo it (M1.5 showed a raw JSON reply) or misread ISO times. Tools whose
results have no short wording (web search, read page) are passed as JSON.
Agent summaries (written by the LLM) and failed calls are left out. If an agent
ran but no tool call succeeded, the code adds NO_ACTION_NOTE, so the reply
cannot claim that something was done.
Also written by code: a question the agent must ask (stopped "ask"), every 🔴
call refused for lack of approval, named by event, and after a cancel or
clear request, the events still on the calendar (M1.7 t10).
The reply language comes from the language tag in the state (M1.8), as the
last line the model reads; today's date is written in by code. A
Devanagari reply to a Roman-script message is asked for again once, in Roman
letters. A single successful write gets a code-written reply instead, with no
LLM call (leo/graph/quick_reply.py).
"""

import json
import re
from collections.abc import Callable
from datetime import date

from langchain_core.messages import AIMessage, convert_to_openai_messages

from leo.graph.quick_reply import quick_reply
from leo.graph.result_words import refused_words, result_in_words, still_on_calendar
from leo.graph.state import LeoState, latest_user_text
from leo.language.calendar_words import asks_to_cancel
from leo.language.time_parser import current_time
from leo.llm.prompts import load_prompt

PROMPT = load_prompt("responder")
NO_ACTION_NOTE = "nothing was done and no result is available"
LANGUAGES = {
    "en": "English",
    "hinglish": "Hinglish (Hindi and English mixed, written only in Roman letters, never "
                "Devanagari)",
    "hi": "Hindi",
}
RETRY_NOTE = "Write that reply again in Roman (English) letters only, with no Devanagari."
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


# True when a tool step succeeded (its result is not an {"error": ...} dict).
def succeeded(step: dict) -> bool:
    result = step.get("result")
    return not (isinstance(result, dict) and "error" in result)


# One fact for a successful step: its words, or the tool name and JSON result.
def step_fact(step: dict) -> str:
    words = result_in_words(step["tool"], step["result"])
    if words is not None:
        return words
    return f"{step['tool']} -> {json.dumps(step['result'], ensure_ascii=False)}"


# One line per fact, by agent: successful results, refusals, questions, notes.
def fact_lines(agent_results: dict, asked_cancel: bool = False) -> list[str]:
    lines = []
    for agent, outcome in agent_results.items():
        steps = outcome.get("steps", []) if isinstance(outcome, dict) else []
        good = [s for s in steps if succeeded(s)]
        if not good:
            lines.append(f"- {agent}: {NO_ACTION_NOTE}.")
        lines += [f"- {agent}: {step_fact(s)}" for s in good]
        lines += [f"- {agent}: {line}" for line in refused_words(steps)]
        still = still_on_calendar(steps, asked_cancel) if agent == "calendar" else None
        if still:
            lines.append(f"- {agent}: {still}")
        if isinstance(outcome, dict) and outcome.get("stopped") == "ask":
            lines.append(f"- {agent}: ask the user this question: {outcome.get('summary', '')}")
    return lines


# Today's date: the one an agent worked with (a check can fix it), else today in IST.
def today_of(agent_results: dict) -> date:
    for outcome in agent_results.values():
        if isinstance(outcome, dict) and outcome.get("today"):
            return date.fromisoformat(outcome["today"])
    return current_time().date()


# The messages for the LLM: prompt with today's date, facts (only if an agent
# ran), the conversation, and last the reply language (M1.8 fix round: a
# 4B model follows the last line best).
def responder_messages(state: LeoState) -> list[dict]:
    results = state.get("agent_results") or {}
    today = today_of(results)
    system = f"{PROMPT.render()}\nToday is {today:%A} {today.day} {today:%b %Y}."
    messages = [{"role": "system", "content": system}]
    lines = fact_lines(results, asks_to_cancel(latest_user_text(state)))
    if lines:
        messages.append({"role": "system", "content": "Facts:\n" + "\n".join(lines)})
    language = LANGUAGES.get(state.get("language") or "", "the same language as the user")
    return [*messages, *convert_to_openai_messages(state.get("messages", [])),
            {"role": "system", "content": f"Reply in {language}."}]


# The reply as an AIMessage, with provider, model and timings in response_metadata.
def reply_message(text: str, result=None) -> AIMessage:
    metadata = {"provider": "code", "model": None, "total_s": 0.0, "first_token_s": None,
                "fallback_reason": None}
    if result is not None:
        metadata = {"provider": result.provider, "model": result.model,
                    "total_s": result.total_s, "first_token_s": result.first_token_s,
                    "fallback_reason": result.fallback_reason}
    return AIMessage(content=text, response_metadata=metadata)


# The reply: code-written for a single successful write, else from the LLM,
# asked once more in Roman letters if it came back in Devanagari for Roman text.
def responder_node(state: LeoState, chat: Callable, force_cloud: bool = False) -> dict:
    text = quick_reply(state)
    if text is not None:
        return {"messages": [reply_message(text)]}
    messages = responder_messages(state)
    result = chat(messages, None, force_cloud)
    if state.get("language") in ("en", "hinglish") and DEVANAGARI.search(result.text):
        retry = [*messages, {"role": "assistant", "content": result.text},
                 {"role": "system", "content": RETRY_NOTE}]
        result = chat(retry, None, force_cloud)
    return {"messages": [reply_message(result.text, result)]}
