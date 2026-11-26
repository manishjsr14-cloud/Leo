# M2.3 memory check (2026-11-26 19:12)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); power: plugged in (battery 100 %)
Commit: 4a6f0fc.
Check set: evals/scenarios/m2_3_memory_questions.yaml.
Memory settings: {'search_k': 5, 'recall_k': 3, 'min_similarity': 0.88, 'candidate_subjects': 5}.

**Result: PASSED** (part A Recall@5 >= 0.90 on the original 20 questions).
Fix-round rerun rule, Recall@5 >= 0.90: original 0.90 (reached); fix 0.75 (below).

## Part A (the pass rule): seeded store, real embedder

Facts saved: 33; active memories: 30; replaced: 3.

### Question set: original

| Q | lang | kind | expect | rank in top 5 | similarity | top-1 | in prompt |
|---|---|---|---|---|---|---|---|
| Q01 | hinglish | negation | F31 | 1 | 0.852 | 0.852 | no |
| Q02 | en | negation | F31 | 2 | 0.825 | 0.832 | no |
| Q03 | hinglish | negation | F32 | 1 | 0.845 | 0.845 | no |
| Q04 | en | negation | F33 | 1 | 0.850 | 0.850 | no |
| Q05 | hinglish |  | F03 | 1 | 0.889 | 0.889 | yes |
| Q06 | en |  | F05 | 1 | 0.888 | 0.888 | yes |
| Q07 | hinglish |  | F06 | 2 | 0.839 | 0.858 | no |
| Q08 | en |  | F02 | 1 | 0.881 | 0.881 | yes |
| Q09 | hinglish |  | F09 | 1 | 0.905 | 0.905 | yes |
| Q10 | hinglish |  | F19 | 5 | 0.804 | 0.858 | no |
| Q11 | en |  | F12 | 1 | 0.850 | 0.850 | no |
| Q12 | hinglish | g09 | F22 | 5 | 0.832 | 0.854 | no |
| Q13 | en | g09 | F23 | 1 | 0.913 | 0.913 | yes |
| Q14 | hinglish |  | F26 | 2 | 0.831 | 0.838 | no |
| Q15 | en |  | F20 | 1 | 0.869 | 0.869 | no |
| Q16 | hinglish |  | F18 | missed | - | 0.813 | no |
| Q17 | en |  | F13 | 1 | 0.846 | 0.846 | no |
| Q18 | hinglish |  | F15 | 1 | 0.907 | 0.907 | yes |
| Q19 | en |  | F16 | 1 | 0.876 | 0.876 | no |
| Q20 | hinglish |  | F21 | missed | - | 0.863 | no |

**Recall@5 (original): 18/20 = 0.90** (Hinglish 0.82 of 11); Recall@1 0.65; Recall@3 0.80.
Expected fact among the prompt hints (top 3, similarity >= 0.88): 6/20.

| no-memory | lang | hints given | top-1 similarity |
|---|---|---|---|
| X01 | en | 0 | 0.857 |
| X02 | hinglish | 0 | 0.860 |
| X03 | en | 0 | 0.841 |
| X04 | hinglish | 0 | 0.845 |

### Question set: fix

| Q | lang | kind | expect | rank in top 5 | similarity | top-1 | in prompt |
|---|---|---|---|---|---|---|---|
| R01 | hinglish | cross_language | F10 | missed | - | 0.821 | no |
| R02 | hinglish | cross_language | F12 | missed | - | 0.862 | no |
| R03 | hinglish | cross_language | F25 | 2 | 0.840 | 0.849 | no |
| R04 | hinglish | cross_language | F29 | 5 | 0.833 | 0.843 | no |
| R05 | hinglish | cross_language | F24 | 3 | 0.825 | 0.830 | no |
| R06 | hinglish | cross_language | F02 | 5 | 0.830 | 0.845 | no |
| R07 | en | synonym | F31 | 1 | 0.838 | 0.838 | no |
| R08 | hinglish | synonym | F31 | missed | - | 0.809 | no |
| R09 | en | synonym | F27 | 1 | 0.840 | 0.840 | no |
| R10 | en | synonym | F14 | 1 | 0.866 | 0.866 | no |
| R11 | en | synonym | F16 | 1 | 0.863 | 0.863 | no |
| R12 | en | synonym | F33 | 2 | 0.802 | 0.824 | no |

**Recall@5 (fix): 9/12 = 0.75** (Hinglish 0.57 of 7); Recall@1 0.33; Recall@3 0.58.
Expected fact among the prompt hints (top 3, similarity >= 0.88): 0/12.

| no-memory | lang | hints given | top-1 similarity |
|---|---|---|---|
| Y01 | en | 0 | 0.815 |
| Y02 | hinglish | 0 | 0.874 |
| Y03 | en | 0 | 0.845 |
| Y04 | hinglish | 0 | 0.826 |
| Y05 | en | 0 | 0.817 |
| Y06 | hinglish | 0 | 0.853 |

Threshold rule (fix set, highest no-memory top-1 similarity): 0.88.

## Prompt tokens added by recall (responder prompt, with minus without hints)

| Q | hints | without | with | added | providers |
|---|---|---|---|---|---|
| Q01 | 0 | - | - | 0 | - |
| Q02 | 0 | - | - | 0 | - |
| Q03 | 0 | - | - | 0 | - |
| Q04 | 0 | - | - | 0 | - |
| Q05 | 1 | 326 | 379 | 53 | ollama, ollama |
| Q06 | 1 | 305 | 363 | 58 | ollama, ollama |
| Q07 | 0 | - | - | 0 | - |
| Q08 | 1 | 307 | 361 | 54 | ollama, ollama |
| Q09 | 1 | 329 | 381 | 52 | ollama, ollama |
| Q10 | 0 | - | - | 0 | - |
| Q11 | 0 | - | - | 0 | - |
| Q12 | 0 | - | - | 0 | - |
| Q13 | 1 | 308 | 369 | 61 | ollama, ollama |
| Q14 | 0 | - | - | 0 | - |
| Q15 | 0 | - | - | 0 | - |
| Q16 | 0 | - | - | 0 | - |
| Q17 | 0 | - | - | 0 | - |
| Q18 | 2 | 327 | 393 | 66 | ollama, ollama |
| Q19 | 0 | - | - | 0 | - |
| Q20 | 0 | - | - | 0 | - |

Questions with hints: 6/20; tokens added when hints are given: median 56 (min 52, max 66, n 6).

## Time

- Embedder load: 12.7 s; model warm-up: 2.45 s.
- memory_recall node (embed + search), part A questions: median 17.5 (min 15.0, max 26.2, n 32) ms; part B messages: median 18.7 (min 16.5, max 77.5, n 40) ms.
- memory_write node, message not picked by the word rule: median 0.10 (min 0.09, max 0.13, n 5) ms.
- memory_write node, picked (one extraction call): median 4401 (min 2679, max 5054, n 35) ms; extraction call alone: median 4.41 (min 2.66, max 5.03, n 35) s.
- Word rule on the 42 M1.10 suite messages: 0 picked (0%): [].

## Part B (reported): the real write path with the local model

| id | picked by word rule | remember | subject given | expected subject | write ms |
|---|---|---|---|---|---|
| F01 | yes | True | diet | diet | 5054 |
| F02 | yes | False | - | meeting_time_preference | 4471 |
| F03 | yes | False | - | blood_group | 2682 |
| N01 | yes | False | - | (must not store) | 2679 |
| F04 | yes | True | sister_name | sister_name | 2736 |
| F05 | yes | True | sister_birthday | sister_birthday | 4449 |
| F06 | yes | True | brother_birthday | brother_birthday | 4458 |
| F07 | yes | True | home_city | home_city | 4536 |
| N02 | yes | False | - | (must not store) | 4370 |
| F08 | no | - | - | coffee | 0 |
| F09 | yes | True | allergy | allergy | 4423 |
| F10 | yes | False | - | job | 4353 |
| F11 | yes | False | - | gym_days | 4395 |
| N03 | no | - | - | (must not store) | 0 |
| F12 | yes | False | - | car | 4363 |
| F13 | yes | True | movie_preference | movie_preference | 4431 |
| F14 | yes | False | - | sport | 4350 |
| F15 | yes | True | wife_name | wife_name | 4436 |
| N04 | yes | False | - | (must not store) | 4355 |
| F16 | yes | False | - | doctor | 4353 |
| F17 | yes | False | - | sleep_time | 4382 |
| F18 | no | - | - | wake_time | 0 |
| F19 | yes | True | tea_preference | tea_sugar | 4470 |
| F20 | yes | False | - | son | 4370 |
| N05 | yes | False | - | (must not store) | 4355 |
| F21 | yes | True | cuisine_preference | favourite_cuisine | 4488 |
| F22 | yes | True | headache_trigger | migraine | 4484 |
| F23 | no | - | - | afternoon_energy | 0 |
| F24 | yes | False | - | bank | 4401 |
| N06 | yes | False | - | (must not store) | 4393 |
| F25 | yes | False | - | weekend_hobby | 4384 |
| F26 | yes | True | sugar_intake | father_health | 4544 |
| F27 | yes | False | - | laptop | 4437 |
| F28 | yes | False | - | languages_spoken | 4428 |
| F29 | no | - | - | evening_walk | 0 |
| N07 | yes | False | - | (must not store) | 4381 |
| F30 | yes | False | - | favourite_place | 4384 |
| F31 | yes | True | diet | diet | 4431 |
| F32 | yes | True | home_city | home_city | 4437 |
| F33 | yes | True | tea_preference | coffee | 4461 |

Facts stored: 12/30; facts the word rule did not pick: ['F08', 'F18', 'F23', 'F29']; must-not-store kept out: 7/7 (picked by the word rule: 6).
Replacements done (old text gone, new text stored): 3/3 (F01->F31 ok, F07->F32 ok, F08->F33 ok).
Recall@5 (original) on the store built by the write path: 0.55 (11/20).
Recall@5 (fix) on the store built by the write path: 0.17 (2/12).
Active memories stored: 12.
Extraction LLM calls: 35; providers: ['ollama'].
