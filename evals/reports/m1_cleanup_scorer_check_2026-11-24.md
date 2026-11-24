# M1 cleanup scorer check — 2026-11-24 15:38
Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)
Commit: e768711.
Check set: evals/scenarios/m1_cleanup_language_replies.yaml (version 1), 48 replies. No LLM, no tools.

v1: evals/m1_8_scoring.py language_ok (no 'hi' class: n/a). v2: evals/language_scoring_v2.py reply_language, right when equal to the label.

## Summary

| label | cases | v1 right | v2 right |
|---|---|---|---|
| en | 21 | 20/21 (95.2 %) | 20/21 (95.2 %) |
| hinglish | 19 | 16/19 (84.2 %) | 19/19 (100.0 %) |
| hi | 8 | - | 8/8 (100.0 %) |
| all | 48 | 36/40 (90.0 %) | 47/48 (97.9 %) |

## Cases where v1 or v2 is wrong (4)

- r01 (hinglish): v1 FAIL, v2 hinglish (markers ['baat', 'karein', 'kaise', 'ho']): Hi! Baat karein, kaise ho? 😊
- r06 (hinglish): v1 FAIL, v2 hinglish (markers ['diya']): Timer laga diya.
- r16 (hinglish): v1 FAIL, v2 hinglish (markers ['aapki', 'karunga']): Sure! Main aapki madad karunga.
- r48 (en): v1 FAIL, v2 hinglish (markers ['kal', 'wali']): Sorry, I couldn't find "kal wali PDF".

## All cases

| id | label | v1 | v2 | v2 markers | reply |
|---|---|---|---|---|---|
| r01 | hinglish | FAIL | hinglish | baat, karein, kaise, ho | Hi! Baat karein, kaise ho? 😊 |
| r02 | hinglish | ok | hinglish | theek, hoon, aap, batao | Main theek hoon, aap batao? |
| r03 | hinglish | ok | hinglish | ho, gaya | Ho gaya! |
| r04 | hinglish | ok | hinglish | theek, hai, kar, diya | Theek hai, kar diya. |
| r05 | hinglish | ok | hinglish | haan, baje, ho | Haan, 4 baje free ho. |
| r06 | hinglish | FAIL | hinglish | diya | Timer laga diya. |
| r07 | hinglish | ok | hinglish | kal, mein, ka, hai | Kal Pune mein baarish ka chance 70% hai. |
| r08 | hinglish | ok | hinglish | mein, daal, diya | 'Dentist' Thu 19 Nov, 4:00-5:00 pm calendar mein daal diya. |
| r09 | hinglish | ok | hinglish | yeh, nahi, kar, sakta | Sorry, yeh main nahi kar sakta. |
| r10 | hinglish | ok | hinglish | aapki, hain, aur | Aapki do tasks pending hain: Buy milk aur Pay electricity bill. |
| r11 | hinglish | ok | hinglish | karne, ke, liye, aapki, chahiye | Gym cancel karne ke liye aapki approval chahiye. |
| r12 | hinglish | ok | hinglish | koi, nahi, hai, aaj | Koi meeting nahi hai aaj shaam. |
| r13 | hinglish | ok | hinglish | bilkul, kar, liya | Bilkul, note save kar liya. |
| r14 | hinglish | ok | hinglish | abhi, koi, nahi, mila, kal, karein | Abhi koi free slot nahi mila, kal try karein? |
| r15 | hinglish | ok | hinglish | kuch, aur | Okay, done. Kuch aur? |
| r16 | hinglish | FAIL | hinglish | aapki, karunga | Sure! Main aapki madad karunga. |
| r17 | hinglish | ok | hinglish | baje, ho, gaya | Lonavala trip Saturday subah 7 baje add ho gaya. |
| r18 | en | ok | en |  | Hi! How can I help you today? |
| r19 | en | ok | en |  | Done! Added 'Meeting with Rahul' on Tue 17 Nov, 10:00-11:00 am. |
| r20 | en | ok | en |  | You're free on Thu 19 Nov: 12:00-1:00 pm and 2:00-4:00 pm. |
| r21 | en | ok | en |  | Added 'Doodh' to your tasks. |
| r22 | en | ok | en |  | I checked the forecast for Sat 21 Nov: 5% chance of rain. |
| r23 | en | ok | en |  | Sure. |
| r24 | en | ok | en |  | OK, done. |
| r25 | en | ok | en |  | Timer 'chai' set for 10 minutes. |
| r26 | en | ok | en |  | Your note 'gas cylinder book karna hai' is saved. |
| r27 | en | ok | en |  | Saved the note. |
| r28 | en | ok | en |  | No, it will not rain in Pune tomorrow. (Source: Open-Meteo) |
| r29 | en | ok | en |  | Cancelling 'Gym' needs your approval first; nothing was cancelled yet. |
| r30 | en | ok | en |  | Do you want me to move it to 5 pm? |
| r31 | en | ok | en |  | I'm not sure. Can you say the time again? |
| r32 | en | ok | en |  | The answer is 480. |
| r33 | en | ok | en |  | Your meeting with Rahul is at 10 am in Andheri. |
| r34 | en | ok | en |  | Added 'Sharma ji' on Fri 20 Nov, 6:00-7:00 pm. |
| r35 | en | ok | en |  | The trip to Lonavala was not added because the rain chance is 60%. |
| r36 | hi | n/a | hi |  | नहीं, कल पुणे में बारिश नहीं होगी। बारिश की संभावना 0% है। (स्रोत: Open-Meteo) |
| r37 | hi | n/a | hi |  | ठीक है, कर दिया। |
| r38 | hi | n/a | hi |  | आपका टाइमर 10 मिनट के लिए लग गया। |
| r39 | hi | n/a | hi |  | हो गया! |
| r40 | hi | n/a | hi |  | 'Meeting with Rahul' कल सुबह 10 बजे कैलेंडर में डाल दी। |
| r41 | hi | n/a | hi |  | आपके पास शनिवार को Gym और Call हैं। |
| r42 | hi | n/a | hi |  | मुझे नहीं पता। |
| r43 | hi | n/a | hi |  | 18% of 2450 = 441, यानी जवाब 441 है। |
| r44 | en | ok | en |  | Your main meeting is at 5 pm. Do you want to move it? |
| r45 | en | ok | en |  | Hi Neha, I added it to your list too. |
| r46 | hinglish | ok | hinglish | diya, kuch, aur, chahiye | Ok, kr diya. Kuch aur chahiye? |
| r47 | hinglish | ok | hinglish | haan, ji, ho | Haan ji, ho gya. |
| r48 | en | FAIL | hinglish (wrong) | kal, wali | Sorry, I couldn't find "kal wali PDF". |
