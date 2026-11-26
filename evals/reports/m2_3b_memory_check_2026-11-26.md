# M2.3b memory check (2026-11-26 22:00)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); power: plugged in (battery 100 %)
Commit: e537de0.
Check set: evals/scenarios/m2_3b_memory_set.yaml.
Local model: leo-qwen3. Memory settings: {'search_k': 5, 'recall_k': 3, 'candidate_subjects': 5}.
Database left by the check: leo_data/evals/m2_3b_memory_check_2026-11-26.db. All tools are mocks.

**Result: NOT MET** (at least one part of the done rule missed).

## Done rule, part by part

- met: lasting facts stored: 32/32 = 1.00 (min 0.90)
- met: plans/events stored: 0 (max 0)
- MISSED: cued updates replaced: 0/4
- met: uncued same-topic messages that replaced: 0/3
- MISSED: Recall@5: 12/15 = 0.80 (min 0.90)
- the user judges: unanswerable replies with a don't-know phrase: 3/5; without one (the user judges): ['X02', 'X04']

Lasting facts not stored: none. Plans stored: none.
Cued updates: {'U1': False, 'U2': False, 'U3': False, 'U4': False}.
Replacements by other messages: none.

## Messages

| id | group | stored (subject) | replaced rows | agents | LLM calls | turn s |
|---|---|---|---|---|---|---|
| F01 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 16.8 |
| F02 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 10.9 |
| F03 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.4 |
| F04 | facts | general | - | productivity | supervisor:ollama, agent:ollama, memory:ollama | 11.1 |
| F05 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.3 |
| F06 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.9 |
| F07 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.7 |
| F08 | facts | general | - | productivity | supervisor:ollama, agent:ollama, memory:ollama | 9.1 |
| F09 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.3 |
| F10 | facts | general | - | calendar | supervisor:ollama, agent:ollama, responder:ollama, memory:ollama | 14.7 |
| F11 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.3 |
| F12 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.8 |
| F13 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.1 |
| F14 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.7 |
| F15 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.5 |
| F16 | facts | general | - | productivity | supervisor:ollama, agent:ollama, agent:ollama, memory:ollama | 12.8 |
| F17 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.3 |
| F18 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.3 |
| F19 | facts | general | - | productivity | supervisor:ollama, agent:ollama, memory:ollama | 9.0 |
| F20 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.4 |
| F21 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.4 |
| F22 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 9.0 |
| F23 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.3 |
| F24 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.9 |
| F25 | facts | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.4 |
| P01 | plans | - | - | calendar | supervisor:ollama, agent:ollama | 6.2 |
| P02 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 8.9 |
| P03 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 9.5 |
| P04 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 9.2 |
| P05 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 8.9 |
| P06 | plans | - | - | calendar | supervisor:ollama, agent:ollama | 6.8 |
| P07 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 10.2 |
| P08 | plans | - | - | calendar | supervisor:ollama, agent:ollama | 6.3 |
| N1 | same_topic_no_cue | general | - | productivity | supervisor:ollama, agent:ollama, agent:ollama, memory:ollama | 12.0 |
| N2 | same_topic_no_cue | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 9.0 |
| N3 | same_topic_no_cue | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 8.8 |
| U1 | updates | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 10.4 |
| U2 | updates | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.4 |
| U3 | updates | general | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.6 |
| U4 | updates | general | - | productivity | supervisor:ollama, agent:ollama, agent:ollama, memory:ollama | 15.3 |
| B1 | boundary | general | - | calendar | supervisor:ollama, agent:ollama, memory:ollama | 11.7 |
| B2 | boundary | general | - | productivity | supervisor:ollama, agent:ollama, memory:ollama | 9.1 |
| B3 | boundary | general | - | calendar | supervisor:ollama, agent:ollama, responder:ollama, memory:ollama | 12.4 |
| Q01 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 16.1 |
| Q02 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 13.8 |
| Q03 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.5 |
| Q04 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.6 |
| Q05 | questions | - | - | productivity | supervisor:ollama, agent:ollama, agent:ollama, agent:ollama, responder:ollama | 16.8 |
| Q06 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 15.8 |
| Q07 | questions | - | - | - | supervisor:ollama, responder:ollama | 7.4 |
| Q08 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 16.0 |
| Q09 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, agent:ollama, agent:ollama, responder:ollama | 25.7 |
| Q10 | questions | - | - | - | supervisor:ollama, responder:ollama | 7.1 |
| Q11 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.1 |
| Q12 | questions | - | - | productivity | supervisor:ollama, agent:ollama | 6.3 |
| Q13 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.5 |
| Q14 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 17.4 |
| Q15 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.4 |
| X01 | unanswerable | - | - | - | supervisor:ollama, responder:ollama | 6.2 |
| X02 | unanswerable | - | - | - | supervisor:ollama, responder:ollama | 6.3 |
| X03 | unanswerable | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, agent:ollama, responder:ollama | 21.1 |
| X04 | unanswerable | - | - | - | supervisor:ollama, responder:ollama | 6.6 |
| X05 | unanswerable | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 16.0 |

## Questions (Recall@5; hit3 = among the 3 hints given)

| id | lang | gate | rank in top 5 | hit5 | hit3 |
|---|---|---|---|---|---|
| Q01 | en | True | 1 | True | True |
| Q02 | hinglish | True | 1 | True | True |
| Q03 | en | True | missed | False | False |
| Q04 | hinglish | True | 1 | True | True |
| Q05 | en | True | 3 | True | True |
| Q06 | hinglish | True | 2 | True | True |
| Q07 | en | True | 1 | True | True |
| Q08 | hinglish | True | 1 | True | True |
| Q09 | en | True | 1 | True | True |
| Q10 | hinglish | True | missed | False | False |
| Q11 | en | True | 1 | True | True |
| Q12 | hinglish | True | missed | False | False |
| Q13 | en | True | 1 | True | True |
| Q14 | hinglish | True | 1 | True | True |
| Q15 | en | True | 1 | True | True |

Recall@3 (in the hints): 12/15.

## Unanswerable questions: replies in full

- X01 (gate True, don't-know phrase: True): What's my mother's name?
  > I don't know your mother's name.
- X02 (gate True, don't-know phrase: False): Mera passport number kya hai?
  > Mera passport number nahi hai.
- X03 (gate True, don't-know phrase: True): Which school did I go to?
  > I don't know which school you went to. None of the facts mention a school.
- X04 (gate True, don't-know phrase: False): Mera favourite colour kaunsa hai?
  > Mera favourite colour kya hai? - Main nahi jaanta.
- X05 (gate True, don't-know phrase: True): Do I have any cousins in Delhi?
  > I don't know if you have any cousins in Delhi. That information isn't in the facts I have.

## Boundary group (reported only)

- B1: Mujhe meetings 11 baje ke baad pasand hain. -> stored: ['general']
- B2: Main roz subah 6 baje uthta hoon. -> stored: ['general']
- B3: My mother's birthday is on 12 March. -> stored: ['general']

P07 (Is weekend main Lonavala ja raha hoon.): read as a question by the question rule: True; plan rule: False; stored: no.

## Small talk (reported only, on a copy of the database)

- Main theek hoon -> stored: ['general']
- I agree -> stored: ['general']
- I'm fine, thanks -> stored: ['general']
- I think so -> stored: ['general']
- Haan main aa raha hoon -> stored: ['general']

## M1.10 suite under the word rules

- M1.10 suite messages (42), code rules only: gate opens for 3, a write would be triggered for 1.
  - gate: Am I free tomorrow evening?
  - gate: Am I free tomorrow evening?
  - gate: What's on my calendar on Thursday?
  - write: complete my milk task

## Time

- Embedder load: 27.6 s; model warm-up: 8.88 s.
- Memory extraction call: median 2.76 (min 2.61, max 5.83, n 35) s.
- LLM calls: 193; providers: ['ollama']; fallback calls: 0.
- Turn time, boundary: median 11.7 (min 9.1, max 12.4, n 3) s.
- Turn time, facts: median 8.7 (min 8.1, max 16.8, n 25) s.
- Turn time, plans: median 8.9 (min 6.2, max 10.2, n 8) s.
- Turn time, questions: median 7.4 (min 6.1, max 25.7, n 15) s.
- Turn time, same_topic_no_cue: median 9.0 (min 8.8, max 12.0, n 3) s.
- Turn time, unanswerable: median 6.6 (min 6.2, max 21.1, n 5) s.
- Turn time, updates: median 11.5 (min 10.4, max 15.3, n 4) s.

Message ids -> memory rows: {'F01': 1, 'F02': 2, 'F03': 3, 'F04': 4, 'F05': 5, 'F06': 6, 'F07': 7, 'F08': 8, 'F09': 9, 'F10': 10, 'F11': 11, 'F12': 12, 'F13': 13, 'F14': 14, 'F15': 15, 'F16': 16, 'F17': 17, 'F18': 18, 'F19': 19, 'F20': 20, 'F21': 21, 'F22': 22, 'F23': 23, 'F24': 24, 'F25': 25, 'N1': 26, 'N2': 27, 'N3': 28, 'U1': 29, 'U2': 30, 'U3': 31, 'U4': 32, 'B1': 33, 'B2': 34, 'B3': 35}.
