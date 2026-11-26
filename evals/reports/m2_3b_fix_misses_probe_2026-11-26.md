# M2.3b fix-round misses: the 5 nearest memories (2026-11-26 23:25)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); power: plugged in (battery 100 %)
Commit: f196c5a.
Read-only probe on the database the fix-round check left (m2_3b_memory_check_2026-11-26_fix.db, <temp>/leo_evals/); same search as the check (search_memories, top 5, real embedder). Q10 is the original set's one miss.

## Q17: Mera bhai kya karta hai?
- 0.863 sister_name: Meri behen ka naam Kavya hai.
- 0.862 sister_name: Meri choti behen ka naam Isha hai.
- 0.846 job_role: Mere papa retired teacher hain.
- 0.846 doctor_name: Mera doctor Dr. Mehta hai, Kothrud wala.
- 0.839 food_preference: Mera favourite khana rajma chawal hai.

## Q23: Mujhe kaunsa khana sabse zyada pasand hai?
- 0.878 movie_preference: Mujhe comedy movies bahut pasand hain.
- 0.872 food_preference: Mujhe chai ke saath biscuit bhi pasand hai.
- 0.869 tea_sugar_preference: Mujhe chai bina cheeni ke pasand hai.
- 0.865 movie_preference: Mujhe horror movies pasand nahi hain.
- 0.862 peanut_allergy: Mujhe peanuts se allergy hai.

## Q25: Main kahan rehta hoon?
- 0.867 hand_preference: Main left-handed hoon.
- 0.837 job_role: Ab main tester nahi hoon, ab developer hoon.
- 0.835 languages_known: Main Marathi aur Hindi dono bolta hoon.
- 0.833 job_role: Mere papa retired teacher hain.
- 0.830 hobby: Ab main guitar nahi seekh raha, piano seekh raha hoon.

## Q10: Meri gaadi kaunsi hai?
- 0.868 sister_name: Meri behen ka naam Kavya hai.
- 0.860 sister_name: Meri choti behen ka naam Isha hai.
- 0.820 job_role: Mere papa retired teacher hain.
- 0.819 food_preference: Mera favourite khana rajma chawal hai.
- 0.814 doctor_name: Mera doctor Dr. Mehta hai, Kothrud wala.
