"""Scoring for the M2.3b memory check (evals/scenarios/m2_3b_memory_set.yaml).

Plain functions on the run's records, so they are tested without a model.
How each part is counted was fixed in the set's header before any code:
- a lasting fact (F, N, U) is stored when its turn created a memory row;
- a cued update is replaced when its `replaces` fact's row became inactive
  with replaced_by pointing at the update's row;
- a question counts for Recall@5 when the recall gate opened and one of its
  expected rows is among the 5 nearest active memories;
- an unanswerable reply is flagged "says it doesn't know" by a fixed phrase
  list; any reply without one is left for the user to judge.
"""

LASTING_GROUPS = ("facts", "same_topic_no_cue", "updates")
DONT_KNOW = ("don't know", "do not know", "dont know", "not sure", "haven't told",
             "have not told", "haven't mentioned", "didn't tell", "no information",
             "don't have", "do not have", "pata nahi", "nahi pata", "maloom nahi",
             "nahi maloom", "nahi bataya", "jaankari nahi", "jankari nahi",
             "information nahi", "idea nahi")


# Message id -> the first memory row its turn created (only turns that stored one).
def rows_by_message(records: dict[str, dict]) -> dict[str, int]:
    return {mid: rec["created"][0] for mid, rec in records.items() if rec["created"]}


# Ids of the messages in `groups` whose turn stored nothing.
def not_stored(data: dict, records: dict, groups=LASTING_GROUPS) -> list[str]:
    return [m["id"] for g in groups for m in data[g] if not records[m["id"]]["created"]]


# Ids of the plan messages whose turn stored something.
def plans_stored(data: dict, records: dict) -> list[str]:
    return [m["id"] for m in data["plans"] if records[m["id"]]["created"]]


# For each cued update: True when the fact it updates was replaced by it.
def cued_updates(data: dict, records: dict, rows: dict[int, tuple]) -> dict[str, bool]:
    by_message, out = rows_by_message(records), {}
    for u in data["updates"]:
        old, new = by_message.get(u["replaces"]), by_message.get(u["id"])
        out[u["id"]] = (old is not None and new is not None
                        and rows[old][2] == 0 and rows[old][3] == new)
    return out


# Ids of the uncued same-topic messages whose turn replaced any memory.
def uncued_replaced(data: dict, records: dict) -> list[str]:
    return [n["id"] for n in data["same_topic_no_cue"] if records[n["id"]]["replaced"]]


# Every replacement made by a message that is not a cued update: id -> replaced rows.
def other_replacements(data: dict, records: dict) -> dict[str, list[int]]:
    updates = {u["id"] for u in data["updates"]}
    return {mid: rec["replaced"] for mid, rec in records.items()
            if rec["replaced"] and mid not in updates}


# One question's result: gate, rank of the first expected row in the top 5, hit.
def question_result(question: dict, gate: bool, top5: list[int],
                    by_message: dict[str, int]) -> dict:
    want = {by_message[e] for e in question["expect_any_of"] if e in by_message}
    ranks = [i for i, row in enumerate(top5, 1) if row in want]
    rank = ranks[0] if ranks else None
    return {"id": question["id"], "gate": gate, "rank": rank,
            "hit5": gate and rank is not None, "hit3": gate and rank is not None and rank <= 3}


# True when a reply says Leo does not know (fixed phrase list, case-insensitive).
def says_dont_know(reply: str) -> bool:
    lowered = reply.lower().replace("’", "'")
    return any(p in lowered for p in DONT_KNOW)


# The done rule, part by part: (text, passed, or None when the user must judge).
def done_parts(rule: dict, data: dict, records: dict, rows: dict, questions: list[dict],
               unanswerable: list[dict]) -> list[tuple[str, bool | None]]:
    lasting = sum(len(data[g]) for g in LASTING_GROUPS)
    stored = lasting - len(not_stored(data, records))
    cued = cued_updates(data, records, rows)
    hits = sum(q["hit5"] for q in questions)
    flagged = [x["id"] for x in unanswerable if not x["dont_know"]]
    return [
        ((f"lasting facts stored: {stored}/{lasting} = {stored / lasting:.2f} "
         f"(min {rule['lasting_stored_min']:.2f})"), stored / lasting >= rule["lasting_stored_min"]),
        ((f"plans/events stored: {len(plans_stored(data, records))} "
         f"(max {rule['plans_stored_max']})"),
         len(plans_stored(data, records)) <= rule["plans_stored_max"]),
        (f"cued updates replaced: {sum(cued.values())}/{len(cued)}",
         sum(cued.values()) >= rule["cued_updates_replaced"]),
        ((f"uncued same-topic messages that replaced: {len(uncued_replaced(data, records))}/"
         f"{len(data['same_topic_no_cue'])}"),
         len(uncued_replaced(data, records)) <= rule["uncued_replaced_max"]),
        ((f"Recall@5: {hits}/{len(questions)} = {hits / len(questions):.2f} "
         f"(min {rule['recall_at_5_min']:.2f})"), hits / len(questions) >= rule["recall_at_5_min"]),
        ((f"unanswerable replies with a don't-know phrase: {len(unanswerable) - len(flagged)}/"
         f"{len(unanswerable)}; without one (the user judges): {flagged or 'none'}"),
         True if not flagged else None),
    ]


# The fix-round pass rule, part by part (m2_3b_fixround_set.yaml). `records` holds
# both sets' turns, since its updates replace facts of the first set.
def fix_parts(rule: dict, data: dict, records: dict, rows: dict, questions: list[dict],
              unanswerable: list[dict]) -> list[tuple[str, bool | None]]:
    cued, uncued = cued_updates(data, records, rows), uncued_replaced(data, records)
    plans = plans_stored(data, records)
    talk = [m["id"] for m in data["small_talk"] if records[m["id"]]["created"]]
    hits = sum(q["hit5"] for q in questions)
    flagged = [x["id"] for x in unanswerable if not x["dont_know"]]
    return [
        (f"cued updates replaced: {sum(cued.values())}/{len(cued)} {cued}",
         sum(cued.values()) >= rule["cued_updates_replaced"]),
        (f"uncued same-topic messages that replaced: {uncued or 'none'}",
         len(uncued) <= rule["uncued_replaced_max"]),
        (f"plans stored: {plans or 'none'}", len(plans) <= rule["plans_stored_max"]),
        (f"small-talk lines stored: {talk or 'none'}", len(talk) <= rule["small_talk_stored_max"]),
        ((f"Recall@5 on Q16-Q27: {hits}/{len(questions)} = {hits / len(questions):.2f} "
          f"(min {rule['recall_at_5_min']:.2f})"), hits / len(questions) >= rule["recall_at_5_min"]),
        ((f"unanswerable replies with a don't-know phrase: {len(unanswerable) - len(flagged)}/"
          f"{len(unanswerable)}; without one (the user judges): {flagged or 'none'}"),
         True if not flagged else None),
    ]
