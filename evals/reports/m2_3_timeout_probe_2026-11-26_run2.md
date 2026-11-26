# M2.3 timeout probe (2026-11-26 18:19)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)
Commit: b16e0fc.

| round | free RAM before (MiB) | page file used before | embedder load s | free RAM after | page file used after | Ollama load s | first token s | total s | GPU share |
|---|---|---|---|---|---|---|---|---|---|
| without | 2600 | 705 | - | 2107 | 706 | 5.9 | 8.5 | 8.6 | 1.0 |
| with | 2275 | 706 | 71.9 | 1214 | 723 | 5.8 | 8.3 | 8.4 | 1.0 |
| without | 3119 | 721 | - | 2459 | 721 | 4.9 | 7.4 | 7.5 | 1.0 |
| with | 2518 | 721 | 70.4 | 1382 | 710 | 5.2 | 7.7 | 7.9 | 1.0 |

Free RAM before: for "with" rounds, before the embedder was loaded; the embedder's RAM shows in the "after" columns of that round.
Leo's time limits: first token 20.0 s, total 60.0 s.

Leo's warm-up on a cold model, embedder loaded: result 7.812999999994645, elapsed 7.8 s; loaded right after: [{'name': 'leo-qwen3:latest', 'size_mib': 3076, 'gpu_share': 1.0}]; 60 s later: [{'name': 'leo-qwen3:latest', 'size_mib': 3076, 'gpu_share': 1.0}].
Rounds that failed: none.
