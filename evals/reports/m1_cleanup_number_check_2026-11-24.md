# M1.6 parser check — 2026-11-24 16:05
Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)
Commit: ec07dde. Parser: rules only (no LLM). A time case passes only when status, date, time, assumed_ampm, remind_before_min and ask_about all match.

## cleanup number phrases
File: `evals/scenarios/m1_cleanup_number_phrases.yaml`

**Accuracy: 44/44 = 100.0 %** — target ≥ 95%: **MET**

| section | correct |
|---|---|
| other | 44/44 = 100.0 % |

### Failures (0)

None.

### Ask cases (0)
Every case where ask was expected or returned.

| id | now | text | expected | got | result |
|---|---|---|---|---|---|

### Non-time words read as numbers
Failures where an ambiguous word (ath, bara, bees, che, das, do, saath, sat, sath, tin) was read as a number: none.

## M1.6 phrase file, regression check
File: `evals/scenarios/m1_6_indian_phrases.yaml`

**Accuracy: 112/112 = 100.0 %** — target ≥ 95%: **MET**

| section | correct |
|---|---|
| day words, clock, kal, midnight | 48/48 = 100.0 % |
| weekdays | 21/21 = 100.0 % |
| relative times | 8/8 = 100.0 % |
| reminder offsets | 5/5 = 100.0 % |
| not understood | 4/4 = 100.0 % |
| numbers | 26/26 = 100.0 % |

### Failures (0)

None.

### Ask cases (21)
Every case where ask was expected or returned.

| id | now | text | expected | got | result |
|---|---|---|---|---|---|
| t31 | Sat 2026-11-14 10:00 | kal | ask (kal) | ask (kal) | PASS |
| t32 | Sat 2026-11-14 10:00 | kal saadhe gyarah baje | ask (kal) | ask (kal) | PASS |
| t33 | Sat 2026-11-14 10:00 | kal wali meeting thi, use kal phir rakhna hai | ask (kal) | ask (kal) | PASS |
| t34 | Sat 2026-11-14 10:00 | kal ka call tomorrow hai ya yesterday tha? | ask (kal) | ask (kal) | PASS |
| t35 | Sat 2026-11-14 10:00 | kal Rahul ka call | ask (kal) | ask (kal) | PASS |
| t36 | Sun 2026-11-15 01:00 | kal subah 9 baje meeting hai | ask (midnight) | ask (midnight) | PASS |
| t37 | Sun 2026-11-15 01:00 | kal shaam 5 baje call karna hai | ask (midnight) | ask (midnight) | PASS |
| t38 | Sun 2026-11-15 03:30 | kal raat movie dekhi thi | ask (midnight) | ask (midnight) | PASS |
| t39 | Sun 2026-11-15 00:15 | kal | ask (midnight) | ask (midnight) | PASS |
| t44 | Sun 2026-11-15 01:00 | parso shaam 6 baje meeting hai | ask (midnight) | ask (midnight) | PASS |
| t45 | Sun 2026-11-15 01:00 | tomorrow morning 9 am call | ask (midnight) | ask (midnight) | PASS |
| t46 | Sun 2026-11-15 02:30 | day after tomorrow 11 am dentist | ask (midnight) | ask (midnight) | PASS |
| t47 | Sun 2026-11-15 03:45 | parso | ask (midnight) | ask (midnight) | PASS |
| w09 | Sat 2026-11-14 10:00 | shanivaar ko | ask (weekday) | ask (weekday) | PASS |
| w10 | Sat 2026-11-14 10:00 | Saturday 5 baje | ask (weekday) | ask (weekday) | PASS |
| w13 | Sat 2026-11-14 10:00 | agle ravivaar | ask (weekday) | ask (weekday) | PASS |
| w14 | Sat 2026-11-14 10:00 | next Sunday | ask (weekday) | ask (weekday) | PASS |
| w15 | Sat 2026-11-14 10:00 | next Saturday | ask (weekday) | ask (weekday) | PASS |
| w17 | Tue 2026-11-17 10:00 | agle Friday | ask (weekday) | ask (weekday) | PASS |
| w19 | Tue 2026-11-17 10:00 | mangalvaar shaam 6 baje | ask (weekday) | ask (weekday) | PASS |
| w20 | Tue 2026-11-17 10:00 | agle shanivaar subah 9 baje | ask (weekday) | ask (weekday) | PASS |

### Non-time words read as numbers
Failures where an ambiguous word (ath, bara, bees, che, das, do, saath, sat, sath, tin) was read as a number: none.

## M1.6 held-out set, regression check
File: `evals/scenarios/m1_6_heldout_phrases.yaml`

**Accuracy: 34/34 = 100.0 %** — target ≥ 95%: **MET**

| section | correct |
|---|---|
| day words, clock, kal, midnight | 13/13 = 100.0 % |
| weekdays | 5/5 = 100.0 % |
| relative times | 3/3 = 100.0 % |
| reminder offsets | 2/2 = 100.0 % |
| not understood | 2/2 = 100.0 % |
| numbers | 9/9 = 100.0 % |

### Failures (0)

None.

### Ask cases (6)
Every case where ask was expected or returned.

| id | now | text | expected | got | result |
|---|---|---|---|---|---|
| h09 | Thu 2026-11-19 16:30 | kal Neha se baat | ask (kal) | ask (kal) | PASS |
| h10 | Thu 2026-11-19 16:30 | kal jo PDF bheji thi woh kal wapas bhejni hai | ask (kal) | ask (kal) | PASS |
| h12 | Thu 2026-11-19 16:30 | Thursday ko review hai | ask (weekday) | ask (weekday) | PASS |
| h13 | Thu 2026-11-19 16:30 | next Saturday party hai | ask (weekday) | ask (weekday) | PASS |
| h21 | Fri 2026-11-20 01:30 | kal subah 10 baje meeting hai | ask (midnight) | ask (midnight) | PASS |
| h22 | Fri 2026-11-20 01:30 | tomorrow evening 6 pm gym | ask (midnight) | ask (midnight) | PASS |

### Non-time words read as numbers
Failures where an ambiguous word (ath, bara, bees, che, das, do, saath, sat, sath, tin) was read as a number: none.
