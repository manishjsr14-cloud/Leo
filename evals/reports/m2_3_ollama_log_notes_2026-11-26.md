# M2.3 timeouts: Ollama server log notes (2026-11-26)

Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)
Source: Ollama's own server.log on the laptop (not in the repository; it holds local paths),
read with grep after the runs. Counts below come from that file; no Leo code was changed.

## During the M2.3 check (`m2_3_memory_check_2026-11-26.md`, commit 4aa838a), 17:26-17:55

- 75 requests to `/v1/chat/completions` (1 warm-up + 40 token-count calls + 34 extraction
  calls), every one with status 499 (client closed the connection), after 20.14-20.46 s:
  Leo's first-token limit (`llm.primary.first_token_timeout_s: 20`).
- Each request started a new load of leo-qwen3, and each load was ended by Ollama with
  "client connection closed before llama-server finished loading, aborting load" (75 times).
  So the model was never loaded during the whole run, and every call fell back to Groq.
- In all 75 aborted loads the last llama-server line before the abort was
  "warming up the model with an empty run": the weights were already in VRAM (CUDA0 model
  buffer 2375.91 MiB, KV cache 612 MiB) and the load was in llama-server's own warm-up run.
- Memory Ollama saw at those load starts: system free 1.8-2.5 GiB, free swap 4.9-5.1 GiB;
  GPU available 2.8 GiB.

## During the timeout probes (`m2_3_timeout_probe_2026-11-26.md`, `..._run2.md`), 18:05-18:20

- No load was aborted. Ollama's load_duration was 4.9-5.9 s and the first token came after
  7.4-8.5 s, with and without the e5 embedder loaded (run2), 100 % on the GPU; Leo's own
  warm-up (20 s limit) succeeded in 7.8 s with the embedder loaded.
- Free RAM before the loads was 2275-3119 MiB; page-file use changed by under 20 MiB in
  any round.

## What this shows, and what it does not

- Shown: a cold load that takes longer than about 20 s can never finish while Leo keeps
  sending requests, because each request's 20 s first-token limit aborts the load in progress
  and the next request starts it again from the beginning.
- Not shown: why the loads took more than 18 s during the check but about 5 s an hour
  later. Memory pressure is not supported by these numbers: free RAM was similar in both
  periods (1.8-2.5 GiB vs 2.3-3.1 GiB) and loading the embedder did not slow the load in the
  probes. The embedder itself loaded slowly in every run that day (90.0 s in the check,
  54.8-124.2 s in the probes, against 18.6 s in M2.2), so the machine as a whole may have
  been slow (cause not measured: power mode, disk or background work were not recorded).
