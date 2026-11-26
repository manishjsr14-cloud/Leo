# M2.3b memory check (2026-11-26 23:09)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); power: plugged in (battery 100 %)
Commit: 5059b58.
Check set: evals/scenarios/m2_3b_memory_set.yaml.
Local model: leo-qwen3. Memory settings: {'search_k': 5, 'recall_k': 3, 'candidate_subjects': 5}.
Database left by the check: C:/Users/dell/AppData/Local/Temp/leo_evals/m2_3b_memory_check_2026-11-26_fix.db. All tools are mocks.

**Result: every counted part met; the unanswerable replies need the user's judgement.**

## Done rule, part by part

- met: lasting facts stored: 32/32 = 1.00 (min 0.90)
- met: plans/events stored: 0 (max 0)
- met: cued updates replaced: 4/4
- met: uncued same-topic messages that replaced: 0/3
- met: Recall@5: 14/15 = 0.93 (min 0.90)
- the user judges: unanswerable replies with a don't-know phrase: 3/5; without one (the user judges): ['X02', 'X04']

Lasting facts not stored: none. Plans stored: none.
Cued updates: {'U1': True, 'U2': True, 'U3': True, 'U4': True}.
Replacements by other messages: none.

## Messages

| id | group | stored (subject) | replaced rows | agents | LLM calls | turn s |
|---|---|---|---|---|---|---|
| F01 | facts | blood_group | - | - | supervisor:ollama, responder:ollama, memory:ollama | 16.8 |
| F02 | facts | job_role | - | productivity | supervisor:ollama, agent:ollama, memory:ollama | 13.6 |
| F03 | facts | home_city | - | - | supervisor:ollama, responder:ollama, memory:ollama | 10.8 |
| F04 | facts | peanut_allergy | - | productivity | supervisor:ollama, agent:ollama, memory:ollama | 11.7 |
| F05 | facts | diet | - | - | supervisor:ollama, responder:ollama, memory:ollama | 10.9 |
| F06 | facts | sister_name | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.8 |
| F07 | facts | brother_name | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.3 |
| F08 | facts | tea_sugar_preference | - | productivity | supervisor:ollama, agent:ollama, memory:ollama | 12.2 |
| F09 | facts | car_make_model | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.1 |
| F10 | facts | doctor_name | - | research | supervisor:ollama, agent:ollama, agent:ollama, agent:ollama, responder:ollama, memory:ollama | 29.6 |
| F11 | facts | favorite_cricket_team | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.4 |
| F12 | facts | languages_known | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.8 |
| F13 | facts | car_make_model | - | - | supervisor:ollama, responder:ollama, memory:ollama | 10.9 |
| F14 | facts | movie_preference | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.6 |
| F15 | facts | reminder_preference | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.3 |
| F16 | facts | gym | - | calendar | supervisor:ollama, agent:ollama, responder:ollama, memory:ollama | 17.3 |
| F17 | facts | doctor_name | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.2 |
| F18 | facts | hand_preference | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.3 |
| F19 | facts | hobby | - | productivity | supervisor:ollama, agent:ollama, memory:ollama | 12.0 |
| F20 | facts | pet_name | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.4 |
| F21 | facts | coffee_preference | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.3 |
| F22 | facts | food_preference | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.7 |
| F23 | facts | car_make_model | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.2 |
| F24 | facts | job_role | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.4 |
| F25 | facts | job_role | - | - | supervisor:ollama, responder:ollama, memory:ollama | 10.9 |
| P01 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 9.7 |
| P02 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 8.7 |
| P03 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 9.5 |
| P04 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 9.0 |
| P05 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 9.2 |
| P06 | plans | - | - | calendar | supervisor:ollama, agent:ollama | 6.8 |
| P07 | plans | - | - | calendar | supervisor:ollama, agent:ollama, responder:ollama | 10.3 |
| P08 | plans | - | - | calendar | supervisor:ollama, agent:ollama | 6.3 |
| N1 | same_topic_no_cue | peanut_allergy | - | productivity | supervisor:ollama, agent:ollama, agent:ollama, memory:ollama | 15.2 |
| N2 | same_topic_no_cue | sister_name | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.6 |
| N3 | same_topic_no_cue | movie_preference | - | - | supervisor:ollama, responder:ollama, memory:ollama | 11.2 |
| U1 | updates | diet | [5] | - | supervisor:ollama, responder:ollama, memory:ollama | 11.1 |
| U2 | updates | home_city | [3] | - | supervisor:ollama, responder:ollama, memory:ollama | 12.1 |
| U3 | updates | job_role | [2] | - | supervisor:ollama, responder:ollama, memory:ollama | 11.9 |
| U4 | updates | gym | [16] | productivity | supervisor:ollama, agent:ollama, agent:ollama, memory:ollama | 15.4 |
| B1 | boundary | meeting_preference | - | calendar | supervisor:ollama, agent:ollama, memory:ollama | 12.3 |
| B2 | boundary | wake_time | - | productivity | supervisor:ollama, agent:ollama, memory:ollama | 11.9 |
| B3 | boundary | mother_birthday | - | calendar | supervisor:ollama, agent:ollama, responder:ollama, memory:ollama | 15.1 |
| Q01 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 15.8 |
| Q02 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 14.4 |
| Q03 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.4 |
| Q04 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.5 |
| Q05 | questions | - | - | productivity | supervisor:ollama, agent:ollama, agent:ollama, agent:ollama, responder:ollama | 16.8 |
| Q06 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 15.3 |
| Q07 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, agent:ollama, agent:ollama, responder:ollama | 27.9 |
| Q08 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 16.1 |
| Q09 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 14.2 |
| Q10 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.6 |
| Q11 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.1 |
| Q12 | questions | - | - | productivity | supervisor:ollama, agent:ollama | 6.5 |
| Q13 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.3 |
| Q14 | questions | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 16.1 |
| Q15 | questions | - | - | - | supervisor:ollama, responder:ollama | 6.4 |
| X01 | unanswerable | - | - | - | supervisor:ollama, responder:ollama | 6.2 |
| X02 | unanswerable | - | - | - | supervisor:ollama, responder:ollama | 6.1 |
| X03 | unanswerable | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, agent:ollama, responder:ollama | 21.4 |
| X04 | unanswerable | - | - | - | supervisor:ollama, responder:ollama | 6.7 |
| X05 | unanswerable | - | - | research | supervisor:ollama, agent:ollama, agent:ollama, responder:ollama | 15.8 |

## Questions (Recall@5; hit3 = among the 3 hints given)

| id | lang | gate | rank in top 5 | hit5 | hit3 |
|---|---|---|---|---|---|
| Q01 | en | True | 1 | True | True |
| Q02 | hinglish | True | 1 | True | True |
| Q03 | en | True | 2 | True | True |
| Q04 | hinglish | True | 1 | True | True |
| Q05 | en | True | 1 | True | True |
| Q06 | hinglish | True | 3 | True | True |
| Q07 | en | True | 1 | True | True |
| Q08 | hinglish | True | 1 | True | True |
| Q09 | en | True | 1 | True | True |
| Q10 | hinglish | True | missed | False | False |
| Q11 | en | True | 1 | True | True |
| Q12 | hinglish | True | 1 | True | True |
| Q13 | en | True | 1 | True | True |
| Q14 | hinglish | True | 1 | True | True |
| Q15 | en | True | 1 | True | True |

Recall@3 (in the hints): 14/15.

## Unanswerable questions: replies in full

- X01 (gate True, don't-know phrase: True): What's my mother's name?
  > I don't know your mother's name.
- X02 (gate True, don't-know phrase: False): Mera passport number kya hai?
  > Mera passport number nahi hai.
- X03 (gate True, don't-know phrase: True): Which school did I go to?
  > I don't know which school you went to. That information is not in the facts or memories provided.
- X04 (gate True, don't-know phrase: False): Mera favourite colour kaunsa hai?
  > Mera favourite colour kaunsa hai? - Main nahi jaanta, kabhi nahi kaha tha.
- X05 (gate True, don't-know phrase: True): Do I have any cousins in Delhi?
  > I don't have any information about cousins in Delhi.

## Boundary group (reported only)

- B1: Mujhe meetings 11 baje ke baad pasand hain. -> stored: ['meeting_preference']
- B2: Main roz subah 6 baje uthta hoon. -> stored: ['wake_time']
- B3: My mother's birthday is on 12 March. -> stored: ['mother_birthday']

P07 (Is weekend main Lonavala ja raha hoon.): read as a question by the question rule: True; plan rule: False; stored: no.

## Small talk (reported only, on a copy of the database)

- Main theek hoon -> stored: no
- I agree -> stored: no
- I'm fine, thanks -> stored: no
- I think so -> stored: no
- Haan main aa raha hoon -> stored: no

## M1.10 suite under the word rules

- M1.10 suite messages (42), code rules only: gate opens for 3, a write would be triggered for 0.
  - gate: Am I free tomorrow evening?
  - gate: Am I free tomorrow evening?
  - gate: What's on my calendar on Thursday?

## Time

- Embedder load: 66.2 s; model warm-up: 9.98 s.
- Memory extraction call: median 5.56 (min 5.05, max 6.03, n 35) s.
- LLM calls: 198; providers: ['ollama']; fallback calls: 0.
- Turn time, boundary: median 12.3 (min 11.9, max 15.1, n 3) s.
- Turn time, facts: median 11.4 (min 10.8, max 29.6, n 25) s.
- Turn time, plans: median 9.1 (min 6.3, max 10.3, n 8) s.
- Turn time, questions: median 14.2 (min 6.1, max 27.9, n 15) s.
- Turn time, same_topic_no_cue: median 11.6 (min 11.2, max 15.2, n 3) s.
- Turn time, unanswerable: median 6.7 (min 6.1, max 21.4, n 5) s.
- Turn time, updates: median 12.0 (min 11.1, max 15.4, n 4) s.

Message ids -> memory rows: {'F01': 1, 'F02': 2, 'F03': 3, 'F04': 4, 'F05': 5, 'F06': 6, 'F07': 7, 'F08': 8, 'F09': 9, 'F10': 10, 'F11': 11, 'F12': 12, 'F13': 13, 'F14': 14, 'F15': 15, 'F16': 16, 'F17': 17, 'F18': 18, 'F19': 19, 'F20': 20, 'F21': 21, 'F22': 22, 'F23': 23, 'F24': 24, 'F25': 25, 'N1': 26, 'N2': 27, 'N3': 28, 'U1': 29, 'U2': 30, 'U3': 31, 'U4': 32, 'B1': 33, 'B2': 34, 'B3': 35}.
