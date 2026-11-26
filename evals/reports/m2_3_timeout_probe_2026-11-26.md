# M2.3 timeout probe (2026-11-26 18:12)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)
Commit: 6e85615.

| round | free RAM before (MiB) | page file used before | embedder load s | free RAM after | page file used after | Ollama load s | first token s | total s | GPU share |
|---|---|---|---|---|---|---|---|---|---|
| without | 2386 | 646 | 124.2 | 1589 | 815 | 5.2 | 7.8 | 13.7 | 1.0 |
| with | 2764 | 815 | 62.1 | 1661 | 819 | 5.5 | 8.0 | 8.2 | 1.0 |
| without | 2787 | 819 | 56.1 | 1658 | 849 | 5.2 | 7.8 | 7.9 | 1.0 |
| with | 2892 | 849 | 55.9 | 1722 | 847 | 5.2 | 7.8 | 7.9 | 1.0 |

Free RAM before: for "with" rounds, before the embedder was loaded; the embedder's RAM shows in the "after" columns of that round.
Leo's time limits: first token 20.0 s, total 60.0 s.

Leo's warm-up on a cold model, embedder loaded: result 7.89100000000326, elapsed 7.9 s; loaded right after: [{'name': 'leo-qwen3:latest', 'size_mib': 3076, 'gpu_share': 1.0}]; 60 s later: [{'name': 'leo-qwen3:latest', 'size_mib': 3076, 'gpu_share': 1.0}].
Rounds that failed: none.
