# M2.3b plan-rule follow-up check (2026-11-27 21:43)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); power: plugged in (battery 100 %)
Commit: 8834e9e.
Check set: evals/scenarios/m2_3b_plans_set.yaml.
Now for every turn: 2026-11-27T09:00:00+05:30. Local model: leo-qwen3.
Database left by the check: C:/Users/dell/AppData/Local/Temp/leo_evals/m2_3b_plans_check_2026-11-27.db. All tools are mocks.

**Result: PASSED** (every part of the done rule met).

## Pass rule, part by part

- met: plans stored: 0 of 8 (max 0; stored: none)
- met: facts stored: 6 of 6 (min 6; not stored: none)

## Messages

"Kept out by" is the first rule of the write path that keeps the message out, read by code; "stored" is what the run wrote. Messages where the two disagree: none.

| id | group | message | stored (subject) | kept out by (code, write-path order) | plan rule alone | agents | turn s |
|---|---|---|---|---|---|---|---|
| P12 | plans | I'm meeting Rohan this evening. | no | plan rule (part of today or weekend) | plan rule (part of today or weekend) | calendar | 9.8 |
| P13 | plans | Tonight I'm watching the match at a friend's place. | no | plan rule (part of today or weekend) | plan rule (part of today or weekend) | calendar | 11.4 |
| P14 | plans | I'll call the plumber later today. | no | plan rule (part of today or weekend) | plan rule (part of today or weekend) | calendar | 8.8 |
| P15 | plans | This morning I have to submit the report. | no | plan rule (part of today or weekend) | plan rule (part of today or weekend) | productivity | 7.4 |
| P16 | plans | Aaj dopahar main bank jaunga. | no | plan rule (part of today or weekend) | plan rule (part of today or weekend) | calendar | 9.1 |
| P17 | plans | Is weekend hum Goa ja rahe hain. | no | no first-person word | plan rule (part of today or weekend) | calendar | 9.2 |
| P18 | plans | This weekend I'm visiting my parents. | no | plan rule (part of today or weekend) | plan rule (part of today or weekend) | calendar | 6.1 |
| P19 | plans | Aaj raat dinner bahar hai. | no | no first-person word | plan rule (part of today or weekend) | calendar | 9.5 |
| F40 | facts | I usually go running in the evening. | evening_activity | - | no | productivity | 13.0 |
| F41 | facts | Main raat ko late sota hoon. | evening_activity | - | no | productivity | 11.6 |
| F42 | facts | I prefer calls in the afternoon. | evening_activity | - | no | calendar | 9.4 |
| F43 | facts | Mujhe subah ki chai bahut pasand hai. | morning_chai_preference | - | no | - | 9.1 |
| F44 | facts | I always work best in the morning. | morning_chai_preference | - | no | productivity | 11.7 |
| F45 | facts | On weekends I play badminton. | sport | - | no | productivity | 8.8 |
| P10 | reported only | I'm going to the bank this afternoon. | no | plan rule (part of today or weekend) | plan rule (part of today or weekend) | calendar | 9.2 |
| R1 | reported only | Is saal se main Marathi classes le raha hoon. | language_class | - | no | productivity | 9.2 |
| P07 | reported only | Is weekend main Lonavala ja raha hoon. | no | plan rule (part of today or weekend) | plan rule (part of today or weekend) | calendar | 9.1 |
