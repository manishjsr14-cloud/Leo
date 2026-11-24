"""M1 cleanup item 6: read_page with the pinned address, on the real internet.

  python -m evals.m1_cleanup_read_page_check evals/reports/m1_cleanup_read_page_check_<date>.md

Fetches a few fixed public pages with the real read_page (system resolver,
real httpx client) to show that pinning keeps https working: the TLS name and
certificate check use the host name although the connection goes to its IP.
Expected results, written before the run:
  - https://example.com/               page text returned
  - http://github.com/                 redirect to https followed, page text returned
  - https://wrong.host.badssl.com/     refused: the certificate is for another name
  - http://localhost/                  refused before any request: not public
No personal data is sent. Writes a new report; never overwrites one.
"""

import sys
from datetime import datetime
from pathlib import Path

import httpx

from evals.m1_6_parser_check import git_state
from evals.machine import machine_line
from leo.config import load_config
from leo.tools.base import ToolError
from leo.tools.real.web import web_functions
from leo.tools.research_args import ReadPageArgs

CASES = [("https://example.com/", "text"), ("http://github.com/", "text"),
         ("https://wrong.host.badssl.com/", "refused"), ("http://localhost/", "refused")]


# Run read_page on one URL: (outcome "text" or "refused", detail).
def try_url(read_page, url: str) -> tuple[str, str]:
    try:
        out = read_page(ReadPageArgs(url=url))
    except ToolError as error:
        return "refused", str(error)
    return "text", f"final url {out['url']}, {len(out['text'])} characters (wrapped)"


# Fetch every case and write the report.
def main() -> None:
    out = Path(sys.argv[1])
    if out.exists():
        sys.exit(f"{out} already exists; earlier reports are never rewritten.")
    settings = load_config().research
    with httpx.Client(timeout=settings.timeout_s) as client:
        read_page = web_functions(client, settings)["read_page"]
        rows = [(url, want, *try_url(read_page, url)) for url, want in CASES]
    lines = [f"# M1 cleanup read_page check — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             machine_line(), f"Commit: {git_state()}.",
             ("Real read_page, system resolver, real network; each request pinned to the "
              "checked address."), "",
             f"**Matches expected: {sum(want == got for _, want, got, _ in rows)}/{len(rows)}**",
             "", "| url | expected | got | detail |", "|---|---|---|---|"]
    lines += [f"| {url} | {want} | {got}{'' if got == want else ' (UNEXPECTED)'} | "
              f"{detail.replace('|', '/')} |" for url, want, got, detail in rows]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
