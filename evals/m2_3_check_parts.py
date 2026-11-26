"""The measured parts of the M2.3 memory check (run by evals/m2_3_memory_check.py).

part_a: facts saved with their subjects, then Recall@5 (the pass rule; no LLM).
token_cost: each question's reply prompt with and without its hints, on the
local model; the prompt_tokens difference is what recall adds.
part_b / summarise_b: every message through the real memory nodes with the
local model, then what was stored, replaced and kept out.
"""

import time
from datetime import datetime

from langchain_core.messages import HumanMessage

from evals import m2_3_check_helpers as h
from leo.graph.memory_nodes import memory_recall_node, memory_write_node
from leo.graph.responder import responder_messages
from leo.language.memory_words import worth_remembering
from leo.language.normalize import language_tag
from leo.llm import gateway
from leo.memory.memories import all_memories, pick_hints, save_memory, search_memories


# Milliseconds since `start` (a perf_counter value).
def ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


# Search every question in `bank`: rank of the expected fact, hints, recall node time.
def score_questions(bank, data: dict) -> tuple[list[dict], list[float]]:
    facts, rows, times = {f["id"]: f for f in data["facts"]}, [], []
    for q in data["questions"]:
        start = time.perf_counter()
        hints = memory_recall_node({"messages": [HumanMessage(q["text"])]}, bank)["memories"]
        times.append(ms(start))
        found = search_memories(bank, bank.embedder.embed_query(q["text"]), 5)
        texts, want = [m.text for m in found], facts[q["expect"]]["fact"]
        rank = h.rank_of(want, texts)
        rows.append({**q, "rank": rank, "hints": hints, "in_prompt": want in hints,
                     "similarity": found[rank - 1].similarity if rank else None,
                     "top1": found[0].similarity if found else None})
    return rows, times


# Part A: seed the store from the set, score the questions and the no-memory ones.
def part_a(bank, data: dict) -> tuple[dict, list[float]]:
    replaced = 0
    for f in data["facts"]:
        replaced += save_memory(bank, f["subject"], f["fact"], f["lang"], datetime.now())[1]
    rows, times = score_questions(bank, data)
    no_memory = []
    for x in data["no_memory_questions"]:
        found = search_memories(bank, bank.embedder.embed_query(x["text"]), 5)
        no_memory.append({**x, "hints": len(pick_hints(found, bank.cfg)),
                          "best": found[0].similarity if found else None})
    return {"saved": len(data["facts"]), "stored": len(all_memories(bank)), "replaced": replaced,
            "recall_k": bank.cfg.recall_k, "min_similarity": bank.cfg.min_similarity,
            "questions": rows, "no_memory": no_memory}, times


# Prompt tokens each question's reply prompt gains from its hints (local model).
def token_cost(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if not r["hints"]:
            out.append({"id": r["id"], "hints": 0, "added": 0, "note": "no hints, no block"})
            continue
        state = {"messages": [HumanMessage(r["text"])], "language": r["lang"]}
        plain = gateway.chat(responder_messages(state))
        hinted = gateway.chat(responder_messages({**state, "memories": r["hints"]}))
        out.append({"id": r["id"], "hints": len(r["hints"]), "without": plain.prompt_tokens,
                    "with": hinted.prompt_tokens, "providers": [plain.provider, hinted.provider],
                    "added": (hinted.prompt_tokens or 0) - (plain.prompt_tokens or 0)})
    return out


# Part B: every message through the real recall and write nodes with the local model.
def part_b(bank, data: dict) -> tuple[list[dict], list]:
    calls = []

    # The real gateway, recording each result.
    def chat(messages, output_model=None, force_cloud=False):
        calls.append(gateway.chat(messages, output_model, force_cloud))
        return calls[-1]

    items = {i["id"]: i for i in data["facts"] + data["must_not_store"]}
    rows = []
    for item_id in data["write_order"]:
        text, before = items[item_id]["text"], len(calls)
        state = {"messages": [HumanMessage(text)], "language": language_tag(text)}
        start = time.perf_counter()
        memory_recall_node(state, bank)
        recall_ms, start = ms(start), time.perf_counter()
        memory_write_node(state, bank, chat)
        decision = calls[-1].parsed if len(calls) > before else None
        rows.append({"id": item_id, "triggered": worth_remembering(text), "recall_ms": recall_ms,
                     "write_ms": ms(start), "expected_subject": items[item_id].get("subject"),
                     "remember": decision.remember if decision else None,
                     "subject": decision.subject if decision else None})
    return rows, calls


# Summarise part B: stored facts, kept-out messages, replacements, Recall@5.
def summarise_b(bank, data: dict, rows: list[dict], calls: list) -> dict:
    stored = {r["text"] for r in all_memories(bank)}
    facts = {f["id"]: f for f in data["facts"]}
    pairs = [(f["replaces"], f["id"]) for f in data["facts"] if "replaces" in f]
    ok = [f"{old}->{new} {'ok' if facts[old]['fact'] not in stored and facts[new]['fact'] in stored else 'NOT done'}"
          for old, new in pairs]
    q_rows, _ = score_questions(bank, data)
    current = [f for f in data["facts"] if f["id"] not in {o for o, _ in pairs}]
    return {"facts": len(current), "facts_stored": sum(f["fact"] in stored for f in current),
            "facts_not_picked": [r["id"] for r in rows if r["id"][0] == "F" and not r["triggered"]],
            "must_not": len(data["must_not_store"]),
            "kept_out": sum(n["text"] not in stored for n in data["must_not_store"]),
            "must_not_picked": sum(r["triggered"] for r in rows if r["id"][0] == "N"),
            "replace_pairs": len(pairs), "replaced_ok": sum(x.endswith(" ok") for x in ok),
            "replace_detail": ok, "recall5": h.recall_at(q_rows, 5),
            "hits": sum(1 for r in q_rows if r["rank"]), "questions": len(q_rows),
            "stored": len(stored), "calls": len(calls),
            "providers": sorted({c.provider for c in calls}),
            "extraction_s": h.spread([c.total_s for c in calls])}
