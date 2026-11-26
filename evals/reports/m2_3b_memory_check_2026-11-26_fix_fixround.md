# M2.3b fix-round check (2026-11-26 23:09)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); power: plugged in (battery 100 %)
Commit: 5059b58.
Check set: evals/scenarios/m2_3b_fixround_set.yaml (run right after evals/scenarios/m2_3b_memory_set.yaml, in the same store; this set decides the fix-round result).
Local model: leo-qwen3. Memory settings: {'search_k': 5, 'recall_k': 3, 'candidate_subjects': 5}.
Database left by the check: C:/Users/dell/AppData/Local/Temp/leo_evals/m2_3b_memory_check_2026-11-26_fix.db. All tools are mocks.

**Result: NOT MET** (at least one part of the done rule missed).

## Pass rule, part by part

- met: cued updates replaced: 3/3 {'U5': True, 'U6': True, 'U7': True}
- met: uncued same-topic messages that replaced: none
- MISSED: plans stored: ['P10']
- met: small-talk lines stored: none
- MISSED: Recall@5 on Q16-Q27: 8/12 = 0.67 (min 0.90)
- the user judges: unanswerable replies with a don't-know phrase: 2/3; without one (the user judges): ['X08']

Not blind: the small-talk rule (rule A) was written after reading S01-S06, so the small-talk part is not an independent result.
Other replacements by fix-round messages: none.

## Messages

| id | group | stored (subject) | replaced rows | agents | LLM calls | turn s |
|---|---|---|---|---|---|---|
| P09 | fix_plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 9.5 |
| P10 | fix_plans | wake_time | - | calendar | supervisor:ollama, agent:ollama, responder:ollama, memory:ollama | 14.9 |
| P11 | fix_plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 9.3 |
| S01 | fix_small_talk | - | - | - | supervisor:ollama, responder:ollama | 5.7 |
| S02 | fix_small_talk | - | - | - | supervisor:ollama, responder:ollama | 5.6 |
| S03 | fix_small_talk | - | - | - | supervisor:ollama, responder:ollama | 5.4 |
| S04 | fix_small_talk | - | - | - | supervisor:ollama, responder:ollama | 5.5 |
| S05 | fix_small_talk | - | - | - | supervisor:ollama, responder:ollama | 6.2 |
| S06 | fix_small_talk | - | - | - | supervisor:ollama, responder:ollama | 5.5 |
| N4 | fix_same_topic_no_cue | brother_name | - | - | supervisor:ollama, responder:ollama, memory:ollama | 10.9 |
| N5 | fix_same_topic_no_cue | food_preference | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.7 |
| U5 | fix_updates | favorite_cricket_team | [11] | - | supervisor:ollama, responder:ollama, memory:ollama | 11.7 |
| U6 | fix_updates | hobby | [19] | productivity | supervisor:ollama, agent:ollama, agent:ollama, memory:ollama | 15.2 |
| U7 | fix_updates | car_make_model | [23] | - | supervisor:ollama, responder:ollama, memory:ollama | 11.8 |
| R1 | fix_reported_only | - | - | productivity | supervisor:ollama, agent:ollama | 6.3 |
| Q16 | fix_questions | - | - | productivity | supervisor:ollama, agent:ollama | 6.3 |
| Q17 | fix_questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 15.8 |
| Q18 | fix_questions | - | - | - | supervisor:ollama, responder:ollama | 6.5 |
| Q19 | fix_questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 16.0 |
| Q20 | fix_questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 13.9 |
| Q21 | fix_questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 13.9 |
| Q22 | fix_questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 15.3 |
| Q23 | fix_questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 15.5 |
| Q24 | fix_questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 14.2 |
| Q25 | fix_questions | - | - | - | supervisor:ollama, responder:ollama | 7.2 |
| Q26 | fix_questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 14.5 |
| Q27 | fix_questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 15.8 |
| X06 | fix_unanswerable | - | - | - | supervisor:ollama, responder:ollama | 6.6 |
| X07 | fix_unanswerable | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 14.8 |
| X08 | fix_unanswerable | - | - | calendar | supervisor:ollama, agent:ollama | 6.2 |

## Questions (Recall@5; hit3 = among the 3 hints given)

| id | lang | question | gate | rank in top 5 | hit5 | hit3 |
|---|---|---|---|---|---|---|
| Q16 | en | Which phone do I use? | True | 1 | True | True |
| Q17 | hinglish | Mera bhai kya karta hai? | True | missed | False | False |
| Q18 | en | What instrument am I learning? | True | 1 | True | True |
| Q19 | hinglish | Main kaunsi IPL team support karta hoon? | True | 3 | True | True |
| Q20 | en | Am I allergic to anything? | True | 1 | True | True |
| Q21 | hinglish | Mere manager ka naam batao. | False | 1 | False | False |
| Q22 | en | What's my sister called? | True | 1 | True | True |
| Q23 | hinglish | Mujhe kaunsa khana sabse zyada pasand hai? | True | missed | False | False |
| Q24 | en | Do I take sugar in my tea? | True | 1 | True | True |
| Q25 | hinglish | Main kahan rehta hoon? | True | missed | False | False |
| Q26 | en | What languages do I speak? | True | 1 | True | True |
| Q27 | hinglish | Mere papa pehle kya the? | True | 1 | True | True |

Recall@3 (in the hints): 8/12.

## Unanswerable questions: replies in full

- X06 (gate True, don't-know phrase: True): What's my wife's name?
  > I don't know your wife's name.
- X07 (gate True, don't-know phrase: True): Meri height kitni hai?
  > Mera height kya hai, main nahi pata. 😊
- X08 (gate True, don't-know phrase: False): When did I last visit a dentist?
  > Nothing on your calendar in Thu 26 Nov (whole day).

## Reported only

- R1 (Is saal se main Marathi classes le raha hoon.): read as a question: True; plan rule: False; stored: no.

## Time (fix-round set)

- Embedder load: 66.2 s; model warm-up: 9.98 s.
- Memory extraction call: median 5.73 (min 5.11, max 5.95, n 6) s.
- LLM calls: 90; providers: ['ollama']; fallback calls: 0.
- Turn time, fix_plans: median 9.5 (min 9.3, max 14.9, n 3) s.
- Turn time, fix_questions: median 14.3 (min 6.3, max 16.0, n 12) s.
- Turn time, fix_reported_only: median 6.3 (min 6.3, max 6.3, n 1) s.
- Turn time, fix_same_topic_no_cue: median 11.3 (min 10.9, max 11.7, n 2) s.
- Turn time, fix_small_talk: median 5.6 (min 5.4, max 6.2, n 6) s.
- Turn time, fix_unanswerable: median 6.6 (min 6.2, max 14.8, n 3) s.
- Turn time, fix_updates: median 11.8 (min 11.7, max 15.2, n 3) s.
