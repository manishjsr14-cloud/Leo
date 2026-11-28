# M2.4 restart check (2026-11-28 23:47)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); power: plugged in (battery 100 %)
Commit: 0f94ac7.
Check set: evals/scenarios/m2_4_restart_set.yaml.
Now for every turn: 2026-11-28T10:00:00+05:30. Local model: leo-qwen3. Memory off; all tools are mocks.
Summary settings: summarize_after 12, keep_messages 6.
Databases left by the check: C:\Users\dell\AppData\Local\Temp\leo_evals\m2_4_restart_check_2026-11-28_summary.db, C:\Users\dell\AppData\Local\Temp\leo_evals\m2_4_restart_check_2026-11-28_no_summary.db.

**Result: PASSED** (every part of the pass rule met, summary variant).

## Pass rule (summary variant)

- met: R5 and R6 (recent) both answered: 2 of 2
- met: at least 3 of R1-R4 (summarized) answered: 4 of 4
- met: after the restart the state has a summary and the same last messages as just before the kill: yes

## Kill and restart

- summary: part 1 hard-killed while waiting for input: yes (exit code 1); part 2 exit code 0
  - before the kill: 8 messages, summary present; after the restart: 8 messages, summary present; same messages: yes; same summary: yes
  - summary after the restart: "- User is planning a trip to Jaipur.  \n- Train number: 12956.  \n- Hotel booking ID: HX4471.  \n- Cousin Tanvi is coming with the user.  \n- No room type, date, or specific plans mentioned for Tanvi.  \n- No details about travel dates, times, or itinerary.  \n- User asked Leo to help with the trip plan; Leo noted missing details.  \n- Leo did not provide any specific action or plan.  \n- Added 'pack the charger' and 'buy a power bank' to user's tasks.  \n- Rain is likely in Jaipur tomorrow, 70% chance (Open-Meteo).  \n- User will stay for three days.  \n- Cab driver's name is Govind.  \n- 18% of 6400 = 1152.  \n- Tanvi does not like spicy food.  \n- Note: Amber Fort tickets online need to be purchased.  \n- Trip budget is 25,000 rupees.  \n- Restaurant: Laxmi Mishthan Bhandar.  \n- Timer 'packing' set for 15 minutes."
- no_summary: part 1 hard-killed while waiting for input: yes (exit code 1); part 2 exit code 0
  - before the kill: 40 messages, summary none; after the restart: 40 messages, summary none; same messages: yes; same summary: yes
  - summary after the restart: '(none)'

## After the restart: summary (judged)

| id | expected | answered | fact was in | reply |
|---|---|---|---|---|
| R5 | B3 | yes | recent | Our seats are in coach B3. |
| R6 | 1:30, 1.30, dedh | yes | recent | Check-in 1:30 baje hai. |
| R1 | 12956 | yes | summary | Train number 12956 tha. |
| R2 | HX4471 | yes | summary | The hotel booking ID was HX4471. |
| R3 | Govind | yes | summary | Cab driver ka naam Govind tha. |
| R4 | 25000, 25,000, 25 hazaar, 25k, 25 thousand | yes | summary | Our trip budget is +25,000 rupees. |

## After the restart: no_summary (reported only)

| id | expected | answered | fact was in | reply |
|---|---|---|---|---|
| R5 | B3 | yes | recent | Our seats are in coach B3. |
| R6 | 1:30, 1.30, dedh | yes | recent | Check-in 1:30 baje hai. |
| R1 | 12956 | NO | recent | Train number nahi diya tha. |
| R2 | HX4471 | yes | recent | Hotel booking ID was HX4471. |
| R3 | Govind | yes | recent | Cab driver ka naam Govind tha. |
| R4 | 25000, 25,000, 25 hazaar, 25k, 25 thousand | yes | recent | Our trip budget is 25,000 rupees. |

## Prompt tokens (reported only)

- summary: 68 LLM calls, prompt tokens 47082 in all (44753 without the summary calls; 0 calls without a count); summary calls 5, 7.4-11.6 s, mean 9.2 s
- no_summary: 61 LLM calls, prompt tokens 58914 in all (58914 without the summary calls; 0 calls without a count); no summary calls

| turn | largest prompt (summary) | largest prompt (no summary) | responder prompt (summary) | responder prompt (no summary) | summary call tokens / s |
|---|---|---|---|---|---|
| P01 | 367 | 367 | 367 | 367 | - |
| P02 | 400 | 389 | 400 | 389 | - |
| P03 | 466 | 450 | 466 | 450 | - |
| P04 | 486 | 469 | 486 | 469 | - |
| P05 | 513 | 503 | ? | ? | - |
| P06 | 614 | 603 | 614 | 603 | - |
| P07 | 585 | 574 | 585 | 574 | 355 / 7.4 |
| P08 | 557 | 609 | 557 | 609 | - |
| P09 | 491 | 550 | ? | ? | - |
| P10 | 646 | 705 | 646 | 705 | - |
| P11 | 660 | 721 | ? | ? | 408 / 7.8 |
| P12 | 616 | 753 | 616 | 753 | - |
| P13 | 738 | 879 | 738 | 879 | - |
| P14 | 688 | 833 | 688 | 833 | - |
| P15 | 721 | 869 | 721 | 869 | 472 / 9.1 |
| P16 | 669 | 907 | ? | ? | - |
| P17 | 724 | 962 | 724 | 962 | - |
| P18 | 759 | 1013 | ? | ? | - |
| P19 | 798 | 1052 | 798 | 1052 | 524 / 10.0 |
| P20 | 711 | 1070 | 711 | 1070 | - |
| R5 | 737 | 1102 | 737 | 1102 | - |
| R6 | 884 | 1402 | 775 | 1142 | - |
| R1 | 1414 | 1358 | 1360 | 1337 | 570 / 11.6 |
| R2 | 862 | 1182 | 720 | 1182 | - |
| R3 | 756 | 1235 | 756 | 1235 | - |
| R4 | 970 | 1478 | 754 | 1233 | - |

## Turns (summary variant)

- P01: Hi Leo, aaj main ek trip plan kar raha hoon.
  - agents: none; tools: none; reply shown after 5.6 s, turn 5.6 s; messages after: 2
  - reply: Hi! Aaj trip plan kar raha ho? Kya destination hai ya kya karna hai? 😊
- P02: We're going to Jaipur, and the train number is 12956.
  - agents: none; tools: none; reply shown after 3.3 s, turn 3.3 s; messages after: 4
  - reply: Train 12956 to Jaipur. Is train ka koi detail nahi diya gaya.
- P03: Hotel ka booking ID HX4471 hai.
  - agents: none; tools: none; reply shown after 3.4 s, turn 3.4 s; messages after: 6
  - reply: Hotel booking ID HX4471. Koi room type ya date nahi diya.
- P04: My cousin Tanvi is coming with us.
  - agents: none; tools: none; reply shown after 3.1 s, turn 3.1 s; messages after: 8
  - reply: Tanvi is coming with you. Any plans for her?
- P05: Add pack the charger to my tasks.
  - agents: productivity; tools: add_task; reply shown after 12.0 s, turn 12.0 s; messages after: 10
  - reply: Added 'pack the charger' to your tasks.
- P06: Will it rain in Jaipur tomorrow?
  - agents: research; tools: get_weather; reply shown after 14.2 s, turn 14.2 s; messages after: 12
  - reply: Yes, rain is likely in Jaipur tomorrow, with a 70% chance (Open-Meteo).
- P07: Hum log teen din rukenge.
  - agents: none; tools: none; reply shown after 4.9 s, turn 12.4 s; messages after: 6
  - reply: You'll stay for three days. Any specific dates or activities planned?
- P08: The cab driver's name is Govind.
  - agents: none; tools: none; reply shown after 4.5 s, turn 4.5 s; messages after: 8
  - reply: The cab driver's name is Govind.
- P09: What is 18% of 6400?
  - agents: productivity; tools: calculate; reply shown after 5.5 s, turn 5.5 s; messages after: 10
  - reply: 18% of 6400 = 1152.
- P10: Tanvi ko spicy food pasand nahi hai.
  - agents: none; tools: none; reply shown after 3.5 s, turn 3.5 s; messages after: 12
  - reply: Tanvi ne spicy food nahi pasand ki.
- P11: Note kar lo: Amber Fort tickets online lene hain.
  - agents: productivity; tools: add_note; reply shown after 9.4 s, turn 17.2 s; messages after: 6
  - reply: Note save kar diya.
- P12: Our budget for the whole trip is 25000 rupees.
  - agents: none; tools: none; reply shown after 4.2 s, turn 4.2 s; messages after: 8
  - reply: Trip budget is 25,000 rupees.
- P13: Kal Pune mein weather kaisa hoga?
  - agents: research; tools: get_weather; reply shown after 14.3 s, turn 14.3 s; messages after: 10
  - reply: Kali Pune mein weather 70% chance of rain hoga (Open-Meteo).
- P14: I also need to buy a power bank.
  - agents: none; tools: none; reply shown after 4.2 s, turn 4.3 s; messages after: 12
  - reply: You need to buy a power bank.
- P15: The restaurant we picked is called Laxmi Mishthan Bhandar.
  - agents: none; tools: none; reply shown after 3.0 s, turn 12.1 s; messages after: 6
  - reply: The restaurant is Laxmi Mishthan Bhandar.
- P16: Start a 15 minute timer for packing.
  - agents: productivity; tools: start_timer; reply shown after 10.2 s, turn 10.3 s; messages after: 8
  - reply: Timer 'packing' set for 15 minutes.
- P17: Thanks Leo, abhi ke liye itna hi.
  - agents: none; tools: none; reply shown after 4.6 s, turn 4.6 s; messages after: 10
  - reply: Ok, thanks Leo! 😊
- P18: Hotel check-in time is 1:30 pm.
  - agents: calendar; tools: create_event; reply shown after 11.7 s, turn 11.7 s; messages after: 12
  - reply: Done! Added 'Hotel Check-in' on Sat 28 Nov, 1:30-2:30 pm.
- P19: Accha, ek aur baat.
  - agents: none; tools: none; reply shown after 3.4 s, turn 13.5 s; messages after: 6
  - reply: Acha, ek aur baat? 😊
- P20: Our seats are 41 and 42 in coach B3.
  - agents: none; tools: none; reply shown after 5.1 s, turn 5.1 s; messages after: 8
  - reply: Seats 41 and 42 in coach B3 are noted.
- R5: Which coach are our seats in?
  - agents: productivity; tools: list_notes; reply shown after 19.6 s, turn 19.6 s; messages after: 10
  - reply: Our seats are in coach B3.
- R6: Check-in kitne baje hai?
  - agents: productivity; tools: none; reply shown after 21.2 s, turn 21.2 s; messages after: 12
  - reply: Check-in 1:30 baje hai.
- R1: Train number kya tha?
  - agents: research; tools: web_search, web_search, read_page, web_search; reply shown after 35.0 s, turn 46.5 s; messages after: 6
  - reply: Train number 12956 tha.
- R2: What was the hotel booking ID?
  - agents: productivity; tools: list_tasks, list_notes; reply shown after 31.5 s, turn 31.5 s; messages after: 8
  - reply: The hotel booking ID was HX4471.
- R3: Cab driver ka naam kya bataya tha maine?
  - agents: productivity; tools: list_notes; reply shown after 17.8 s, turn 17.8 s; messages after: 10
  - reply: Cab driver ka naam Govind tha.
- R4: What's our budget for the trip?
  - agents: productivity; tools: none; reply shown after 33.4 s, turn 33.4 s; messages after: 12
  - reply: Our trip budget is +25,000 rupees.
