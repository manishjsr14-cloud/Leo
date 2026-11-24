# M2.2 embedder check (2026-11-24 17:16)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)
Commit: 279a83c.

Result: FAILED under rule B (24/36 sentences pass). Failing: g04.en, g04.hinglish, g04.hi, g09.en, g09.hi, g10.en, g10.hinglish, g10.hi, g11.hi, g12.en, g12.hinglish, g12.hi.

- Model: intfloat/multilingual-e5-small, device cpu, 384 dimensions
- Cache: models/hf_cache (project folder), 470 MiB on disk; already cached before this run: yes
- Reload in a fresh process with HF_HUB_OFFLINE=1: offline load ok
- Load time: 18.6 s; first message after load: 51 ms
- One message (median of 20 after a warm-up): 19.9 ms (min 18.1, max 39.1); torch threads 4
- RAM of this process: 34 MiB before loading, 1164 after loading (+1130), 1171 after all embeddings (+1137); peak working set 1211 MiB

## Near pairs (same sentence)

| a | b | similarity | note |
|---|---|---|---|
| g01.en | g01.hinglish | 0.847 |  |
| g01.en | g01.hi | 0.906 |  |
| g01.hinglish | g01.hi | 0.911 |  |
| g02.en | g02.hinglish | 0.838 |  |
| g02.en | g02.hi | 0.939 |  |
| g02.hinglish | g02.hi | 0.835 |  |
| g03.en | g03.hinglish | 0.837 |  |
| g03.en | g03.hi | 0.896 |  |
| g03.hinglish | g03.hi | 0.906 |  |
| g04.en | g04.hinglish | 0.925 |  |
| g04.en | g04.hi | 0.855 |  |
| g04.hinglish | g04.hi | 0.858 |  |
| g05.en | g05.hinglish | 0.865 |  |
| g05.en | g05.hi | 0.862 |  |
| g05.hinglish | g05.hi | 0.908 |  |
| g06.en | g06.hinglish | 0.872 |  |
| g06.en | g06.hi | 0.928 |  |
| g06.hinglish | g06.hi | 0.868 |  |
| g07.en | g07.hinglish | 0.881 |  |
| g07.en | g07.hi | 0.906 |  |
| g07.hinglish | g07.hi | 0.933 |  |
| g08.en | g08.hinglish | 0.837 |  |
| g08.en | g08.hi | 0.892 |  |
| g08.hinglish | g08.hi | 0.905 |  |
| g09.en | g09.hinglish | 0.757 |  |
| g09.en | g09.hi | 0.886 |  |
| g09.hinglish | g09.hi | 0.834 |  |
| g10.en | g10.hinglish | 0.850 |  |
| g10.en | g10.hi | 0.873 |  |
| g10.hinglish | g10.hi | 0.890 |  |
| g11.en | g11.hinglish | 0.906 |  |
| g11.en | g11.hi | 0.904 |  |
| g11.hinglish | g11.hi | 0.921 |  |
| g12.en | g12.hinglish | 0.843 |  |
| g12.en | g12.hi | 0.849 |  |
| g12.hinglish | g12.hi | 0.853 |  |

## Far pairs (different meaning, scored)

| a | b | similarity | note |
|---|---|---|---|
| g01.en | g05.en | 0.821 |  |
| g02.hinglish | g07.hinglish | 0.782 |  |
| g03.hi | g09.hi | 0.853 |  |
| g06.en | g08.hinglish | 0.752 |  |
| g05.hi | g02.en | 0.742 |  |
| g07.en | g09.hinglish | 0.724 |  |
| g08.en | g06.hi | 0.721 |  |
| g09.en | g01.hinglish | 0.770 |  |
| g01.hi | g07.hi | 0.801 |  |
| g06.hinglish | g05.hinglish | 0.836 |  |
| g08.hi | g03.en | 0.820 |  |
| g03.hinglish | g02.hi | 0.780 |  |
| g04.en | g11.en | 0.887 | hard |
| g04.hinglish | g11.hinglish | 0.874 | hard |
| g04.hi | g11.hi | 0.943 | hard |
| g10.en | g12.en | 0.984 | hard |
| g10.hinglish | g12.hinglish | 0.979 | hard |
| g10.hi | g12.hi | 0.956 | hard |

## Recorded, not scored: kal vs parso

| a | b | similarity | note |
|---|---|---|---|
| g03.en | I have a meeting the day after tomorrow at 5 pm. | 0.985 | lowest near pair of g03.en: 0.837 |
| g03.hinglish | Parso shaam 5 baje meri meeting hai. | 0.989 | lowest near pair of g03.hinglish: 0.837 |
| g03.hi | परसों शाम 5 बजे मेरी मीटिंग है। | 0.978 | lowest near pair of g03.hi: 0.896 |
| g02.hinglish | Parso Delhi mein baarish hogi kya? | 0.939 | lowest near pair of g02.hinglish: 0.835 |

## Rule B per sentence

| sentence | lowest near | highest far | result |
|---|---|---|---|
| g01.en | 0.847 | 0.821 | pass |
| g01.hinglish | 0.847 | 0.770 | pass |
| g01.hi | 0.906 | 0.801 | pass |
| g02.en | 0.838 | 0.742 | pass |
| g02.hinglish | 0.835 | 0.782 | pass |
| g02.hi | 0.835 | 0.780 | pass |
| g03.en | 0.837 | 0.820 | pass |
| g03.hinglish | 0.837 | 0.780 | pass |
| g03.hi | 0.896 | 0.853 | pass |
| g04.en | 0.855 | 0.887 | FAIL |
| g04.hinglish | 0.858 | 0.874 | FAIL |
| g04.hi | 0.855 | 0.943 | FAIL |
| g05.en | 0.862 | 0.821 | pass |
| g05.hinglish | 0.865 | 0.836 | pass |
| g05.hi | 0.862 | 0.742 | pass |
| g06.en | 0.872 | 0.752 | pass |
| g06.hinglish | 0.868 | 0.836 | pass |
| g06.hi | 0.868 | 0.721 | pass |
| g07.en | 0.881 | 0.724 | pass |
| g07.hinglish | 0.881 | 0.782 | pass |
| g07.hi | 0.906 | 0.801 | pass |
| g08.en | 0.837 | 0.721 | pass |
| g08.hinglish | 0.837 | 0.752 | pass |
| g08.hi | 0.892 | 0.820 | pass |
| g09.en | 0.757 | 0.770 | FAIL |
| g09.hinglish | 0.757 | 0.724 | pass |
| g09.hi | 0.834 | 0.853 | FAIL |
| g10.en | 0.850 | 0.984 | FAIL |
| g10.hinglish | 0.850 | 0.979 | FAIL |
| g10.hi | 0.873 | 0.956 | FAIL |
| g11.en | 0.904 | 0.887 | pass |
| g11.hinglish | 0.906 | 0.874 | pass |
| g11.hi | 0.904 | 0.943 | FAIL |
| g12.en | 0.843 | 0.984 | FAIL |
| g12.hinglish | 0.843 | 0.979 | FAIL |
| g12.hi | 0.849 | 0.956 | FAIL |

