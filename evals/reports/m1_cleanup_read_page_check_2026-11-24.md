# M1 cleanup read_page check — 2026-11-24 16:07
Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)
Commit: 62a54b1.
Real read_page, system resolver, real network; each request pinned to the checked address.

**Matches expected: 4/4**

| url | expected | got | detail |
|---|---|---|---|
| https://example.com/ | text | text | final url https://example.com/, 273 characters (wrapped) |
| http://github.com/ | text | text | final url https://github.com/, 1283 characters (wrapped) |
| https://wrong.host.badssl.com/ | refused | refused | could not fetch the page: ConnectTimeout |
| http://localhost/ | refused | refused | refused 'localhost': not a public internet address |
