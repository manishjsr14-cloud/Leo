# M1 cleanup warm-up check — 2026-11-24 16:01
Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)
Commit: 57f1965.
Local model: leo-qwen3. First turn: evals/scenarios/m1_8_language_turns.yaml L04, mock tools. 3 pairs; the model is unloaded before every run.

## Summary

| mode | runs | first token s (avg / min / max) | turn s (avg) |
|---|---|---|---|
| without warm-up | 3 | 9.88 / 9.11 / 10.34 | 15.42 |
| with warm-up | 3 | 3.96 / 3.92 / 3.98 | 9.56 |

## Runs

| pair | mode | warm-up s | first token s | provider | turn s | reply |
|---|---|---|---|---|---|---|
| 1 | without | - | 9.11 | ollama | 14.55 | Added 'bread' to your tasks. |
| 1 | with | 7.81 | 3.92 | ollama | 9.34 | Added 'bread' to your tasks. |
| 2 | without | - | 10.19 | ollama | 15.75 | Added 'bread' to your tasks. |
| 2 | with | 8.67 | 3.98 | ollama | 9.61 | Added 'bread' to your tasks. |
| 3 | without | - | 10.34 | ollama | 15.98 | Added 'bread' to your tasks. |
| 3 | with | 8.73 | 3.98 | ollama | 9.73 | Added 'bread' to your tasks. |
