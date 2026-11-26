# M2.3 memory check (2026-11-26 19:07)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); power: plugged in (battery 100 %)
Commit: a5ebd78.
Check set: evals/scenarios/m2_3_memory_questions.yaml.
Memory settings: {'search_k': 5, 'recall_k': 3, 'min_similarity': 0.8, 'candidate_subjects': 5}.

**Result: PASSED** (part A Recall@5 >= 0.90 on the original 20 questions).
Fix-round rerun rule, Recall@5 >= 0.90: original 0.90 (reached); fix 0.75 (below).

## Part A (the pass rule): seeded store, real embedder

Facts saved: 33; active memories: 30; replaced: 3.

### Question set: original

| Q | lang | kind | expect | rank in top 5 | similarity | top-1 | in prompt |
|---|---|---|---|---|---|---|---|
| Q01 | hinglish | negation | F31 | 1 | 0.852 | 0.852 | yes |
| Q02 | en | negation | F31 | 2 | 0.825 | 0.832 | yes |
| Q03 | hinglish | negation | F32 | 1 | 0.845 | 0.845 | yes |
| Q04 | en | negation | F33 | 1 | 0.850 | 0.850 | yes |
| Q05 | hinglish |  | F03 | 1 | 0.889 | 0.889 | yes |
| Q06 | en |  | F05 | 1 | 0.888 | 0.888 | yes |
| Q07 | hinglish |  | F06 | 2 | 0.839 | 0.858 | yes |
| Q08 | en |  | F02 | 1 | 0.881 | 0.881 | yes |
| Q09 | hinglish |  | F09 | 1 | 0.905 | 0.905 | yes |
| Q10 | hinglish |  | F19 | 5 | 0.804 | 0.858 | no |
| Q11 | en |  | F12 | 1 | 0.850 | 0.850 | yes |
| Q12 | hinglish | g09 | F22 | 5 | 0.832 | 0.854 | no |
| Q13 | en | g09 | F23 | 1 | 0.913 | 0.913 | yes |
| Q14 | hinglish |  | F26 | 2 | 0.831 | 0.838 | yes |
| Q15 | en |  | F20 | 1 | 0.869 | 0.869 | yes |
| Q16 | hinglish |  | F18 | missed | - | 0.813 | no |
| Q17 | en |  | F13 | 1 | 0.846 | 0.846 | yes |
| Q18 | hinglish |  | F15 | 1 | 0.907 | 0.907 | yes |
| Q19 | en |  | F16 | 1 | 0.876 | 0.876 | yes |
| Q20 | hinglish |  | F21 | missed | - | 0.863 | no |

**Recall@5 (original): 18/20 = 0.90** (Hinglish 0.82 of 11); Recall@1 0.65; Recall@3 0.80.
Expected fact among the prompt hints (top 3, similarity >= 0.8): 16/20.

| no-memory | lang | hints given | top-1 similarity |
|---|---|---|---|
| X01 | en | 3 | 0.857 |
| X02 | hinglish | 3 | 0.860 |
| X03 | en | 3 | 0.841 |
| X04 | hinglish | 3 | 0.845 |

### Question set: fix

| Q | lang | kind | expect | rank in top 5 | similarity | top-1 | in prompt |
|---|---|---|---|---|---|---|---|
| R01 | hinglish | cross_language | F10 | missed | - | 0.821 | no |
| R02 | hinglish | cross_language | F12 | missed | - | 0.862 | no |
| R03 | hinglish | cross_language | F25 | 2 | 0.840 | 0.849 | yes |
| R04 | hinglish | cross_language | F29 | 5 | 0.833 | 0.843 | no |
| R05 | hinglish | cross_language | F24 | 3 | 0.825 | 0.830 | yes |
| R06 | hinglish | cross_language | F02 | 5 | 0.830 | 0.845 | no |
| R07 | en | synonym | F31 | 1 | 0.838 | 0.838 | yes |
| R08 | hinglish | synonym | F31 | missed | - | 0.809 | no |
| R09 | en | synonym | F27 | 1 | 0.840 | 0.840 | yes |
| R10 | en | synonym | F14 | 1 | 0.866 | 0.866 | yes |
| R11 | en | synonym | F16 | 1 | 0.863 | 0.863 | yes |
| R12 | en | synonym | F33 | 2 | 0.802 | 0.824 | yes |

**Recall@5 (fix): 9/12 = 0.75** (Hinglish 0.57 of 7); Recall@1 0.33; Recall@3 0.58.
Expected fact among the prompt hints (top 3, similarity >= 0.8): 7/12.

| no-memory | lang | hints given | top-1 similarity |
|---|---|---|---|
| Y01 | en | 3 | 0.815 |
| Y02 | hinglish | 3 | 0.874 |
| Y03 | en | 3 | 0.845 |
| Y04 | hinglish | 3 | 0.826 |
| Y05 | en | 3 | 0.817 |
| Y06 | hinglish | 3 | 0.853 |

Threshold rule (fix set, highest no-memory top-1 similarity): 0.88.

Part A only (--part-a-only): no LLM call, no tokens, no part B.
