# M2.3 memory check (2026-11-26 17:55)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)
Commit: 4aa838a.
Check set: evals/scenarios/m2_3_memory_questions.yaml.
Memory settings: {'search_k': 5, 'recall_k': 3, 'min_similarity': 0.8, 'candidate_subjects': 5}.

**Result: FAILED** (part A Recall@5 >= 0.90 on 20 questions).

## Part A (the pass rule): seeded store, real embedder

Facts saved: 33; memories in the store: 30; replaced: 3.

| Q | lang | kind | expect | rank in top 5 | similarity | top-1 | in prompt |
|---|---|---|---|---|---|---|---|
| Q01 | hinglish | negation | F31 | 2 | 0.836 | 0.839 | yes |
| Q02 | en | negation | F31 | missed | - | 0.827 | no |
| Q03 | hinglish | negation | F32 | 1 | 0.868 | 0.868 | yes |
| Q04 | en | negation | F33 | 1 | 0.856 | 0.856 | yes |
| Q05 | hinglish |  | F03 | 1 | 0.879 | 0.879 | yes |
| Q06 | en |  | F05 | 1 | 0.854 | 0.854 | yes |
| Q07 | hinglish |  | F06 | missed | - | 0.847 | no |
| Q08 | en |  | F02 | 2 | 0.829 | 0.832 | yes |
| Q09 | hinglish |  | F09 | 1 | 0.907 | 0.907 | yes |
| Q10 | hinglish |  | F19 | 5 | 0.808 | 0.875 | no |
| Q11 | en |  | F12 | 1 | 0.823 | 0.823 | yes |
| Q12 | hinglish | g09 | F22 | 2 | 0.848 | 0.848 | yes |
| Q13 | en | g09 | F23 | 1 | 0.904 | 0.904 | yes |
| Q14 | hinglish |  | F26 | 2 | 0.836 | 0.845 | yes |
| Q15 | en |  | F20 | 1 | 0.834 | 0.834 | yes |
| Q16 | hinglish |  | F18 | missed | - | 0.830 | no |
| Q17 | en |  | F13 | 1 | 0.850 | 0.850 | yes |
| Q18 | hinglish |  | F15 | 1 | 0.915 | 0.915 | yes |
| Q19 | en |  | F16 | 1 | 0.848 | 0.848 | yes |
| Q20 | hinglish |  | F21 | missed | - | 0.870 | no |

**Recall@5: 16/20 = 0.80** (Hinglish 0.73 of 11); Recall@1 0.55; Recall@3 0.75.
Expected fact among the prompt hints (top 3, similarity >= 0.8): 15/20.

No-memory questions (recorded, not scored):

| X | lang | hints given | best similarity |
|---|---|---|---|
| X01 | en | 3 | 0.817 |
| X02 | hinglish | 3 | 0.855 |
| X03 | en | 3 | 0.834 |
| X04 | hinglish | 3 | 0.853 |

## Prompt tokens added by recall (responder prompt, with minus without hints)

| Q | hints | without | with | added | providers |
|---|---|---|---|---|---|
| Q01 | 3 | 368 | 452 | 84 | groq, groq |
| Q02 | 3 | 344 | 436 | 92 | groq, groq |
| Q03 | 3 | 365 | 456 | 91 | groq, groq |
| Q04 | 3 | 345 | 441 | 96 | groq, groq |
| Q05 | 3 | 364 | 443 | 79 | groq, groq |
| Q06 | 3 | 346 | 431 | 85 | groq, groq |
| Q07 | 3 | 366 | 447 | 81 | groq, groq |
| Q08 | 3 | 348 | 435 | 87 | groq, groq |
| Q09 | 3 | 367 | 452 | 85 | groq, groq |
| Q10 | 3 | 366 | 446 | 80 | groq, groq |
| Q11 | 3 | 345 | 429 | 84 | groq, groq |
| Q12 | 3 | 368 | 455 | 87 | groq, groq |
| Q13 | 3 | 347 | 433 | 86 | groq, groq |
| Q14 | 3 | 370 | 464 | 94 | groq, groq |
| Q15 | 2 | 346 | 420 | 74 | groq, groq |
| Q16 | 3 | 370 | 461 | 91 | groq, groq |
| Q17 | 3 | 350 | 442 | 92 | groq, groq |
| Q18 | 3 | 365 | 445 | 80 | groq, groq |
| Q19 | 3 | 344 | 438 | 94 | groq, groq |
| Q20 | 3 | 372 | 461 | 89 | groq, groq |

Questions with hints: 20/20; tokens added when hints are given: median 86 (min 74, max 96, n 20).

## Time

- Embedder load: 90.0 s; model warm-up: None s.
- memory_recall node (embed + search), part A questions: median 18.5 (min 15.6, max 70.5, n 20) ms; part B messages: median 31.9 (min 21.2, max 2936.2, n 40) ms.
- memory_write node, message not picked by the word rule: median 0.11 (min 0.07, max 0.59, n 6) ms.
- memory_write node, picked (one extraction call): median 22830 (min 22560, max 23508, n 34) ms; extraction call alone: median 0.74 (min 0.48, max 1.44, n 34) s.
- Word rule on the 42 M1.10 suite messages: 0 picked (0%): [].

## Part B (reported): the real write path with the local model

| id | picked by word rule | remember | subject given | expected subject | write ms |
|---|---|---|---|---|---|
| F01 | yes | True | diet | diet | 23192 |
| F02 | yes | True | meeting_time_preference | meeting_time_preference | 23190 |
| F03 | yes | True | blood_group | blood_group | 22914 |
| N01 | yes | False | - | (must not store) | 22768 |
| F04 | yes | True | sister_name | sister_name | 22926 |
| F05 | yes | True | sister_name | sister_birthday | 22851 |
| F06 | yes | True | brother_birthday | brother_birthday | 22839 |
| F07 | yes | True | home_city | home_city | 22819 |
| N02 | yes | False | - | (must not store) | 22611 |
| F08 | no | - | - | coffee | 1 |
| F09 | yes | True | peanut_allergy | allergy | 22868 |
| F10 | yes | True | occupation | job | 22907 |
| F11 | yes | True | gym_schedule | gym_days | 22648 |
| N03 | no | - | - | (must not store) | 0 |
| F12 | yes | True | car_model | car | 22860 |
| F13 | yes | True | horror_movie_preference | movie_preference | 23117 |
| F14 | yes | True | cricket_preference | sport | 23508 |
| F15 | yes | True | wife_name | wife_name | 22666 |
| N04 | yes | False | - | (must not store) | 22793 |
| F16 | yes | True | doctor_name | doctor | 22769 |
| F17 | yes | True | sleep_time | sleep_time | 23242 |
| F18 | no | - | - | wake_time | 0 |
| F19 | yes | True | sugar_intake | tea_sugar | 22778 |
| F20 | yes | True | child_name | son | 22875 |
| N05 | yes | False | - | (must not store) | 23239 |
| F21 | yes | True | cuisine_preference | favourite_cuisine | 22697 |
| F22 | yes | True | migraine | migraine | 22851 |
| F23 | no | - | - | afternoon_energy | 0 |
| F24 | yes | True | bank_name | bank | 22645 |
| N06 | yes | False | - | (must not store) | 22651 |
| F25 | yes | True | language_learning | weekend_hobby | 22653 |
| F26 | yes | True | father_diabetes | father_health | 22779 |
| F27 | yes | False | - | laptop | 23342 |
| F28 | yes | True | languages_spoken | languages_spoken | 22619 |
| F29 | no | - | - | evening_walk | 0 |
| N07 | yes | False | - | (must not store) | 22821 |
| F30 | yes | True | travel_preference | favourite_place | 22936 |
| F31 | yes | True | diet | diet | 22780 |
| F32 | yes | True | home_city | home_city | 22560 |
| F33 | no | - | - | coffee | 0 |

Facts stored: 24/30; facts the word rule did not pick: ['F08', 'F18', 'F23', 'F29', 'F33']; must-not-store kept out: 7/7 (picked by the word rule: 6).
Replacements done (old text gone, new text stored): 2/3 (F01->F31 ok, F07->F32 ok, F08->F33 NOT done).
Recall@5 on the store built by the write path: 0.70 (14/20); memories stored: 24.
Extraction LLM calls: 34; providers: ['groq'].
