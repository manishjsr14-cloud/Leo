"""Real web tools: web_search (DuckDuckGo via ddgs) and read_page (httpx + trafilatura).

All web text is untrusted: titles, snippets and page text are wrapped in the
context_guard markers before the model sees them. URLs stay plain so the reply
can cite them.

read_page only fetches public addresses. Before every request, including every
redirect hop (followed here by hand, up to research.max_redirects), the host
name is resolved and each address it gives is checked; loopback, private,
link-local, Tailscale (100.64.0.0/10) and other non-public addresses are refused.
So a page cannot send Leo to Radicale, the router or the Tailscale network.
Each request then goes to the address that passed the check (pinned, M1 cleanup
item 6): the URL carries that IP, the Host header carries the name, and for
https the TLS name (SNI and the certificate check) is the name too. The name is
never looked up a second time, so a DNS server that changes its answer between
the check and the request (DNS rebinding) cannot move the request.
"""

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
import trafilatura
from ddgs import DDGS
from ddgs.exceptions import DDGSException

from leo.config import ResearchConfig
from leo.guardrails.context_guard import wrap_untrusted
from leo.tools.base import ToolError
from leo.tools.research_args import ReadPageArgs, WebSearchArgs
from leo.tools.research_tools import SEARCH_SOURCE

# Refused by name, on top of every address that is not globally routable.
BLOCKED_NETWORKS = [ipaddress.ip_network(n) for n in (
    "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16",
    "172.16.0.0/12", "192.168.0.0/16", "::1/128", "fc00::/7", "fe80::/10")]
REDIRECTS = {301, 302, 303, 307, 308}


# All addresses a host name resolves to, as strings (the system resolver).
def resolve_host(host: str) -> list[str]:
    return sorted({info[4][0] for info in socket.getaddrinfo(host, None)})


# True when `host` is written as an IP address (checked as is, not resolved).
def is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


# True when an address must not be fetched: a blocked network or not public.
def is_blocked(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%")[0])  # drop an IPv6 zone like %eth0
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return not ip.is_global or any(ip in net for net in BLOCKED_NETWORKS)


# Raise ToolError unless `url` is http(s) and every address of its host is public.
# Returns the checked addresses.
def check_url(url: str, resolve: Callable[[str], list[str]]) -> list[str]:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ToolError(f"refused {url!r}: only http(s) web addresses")
    try:
        addresses = [parts.hostname] if is_ip(parts.hostname) else resolve(parts.hostname)
    except OSError as error:
        raise ToolError(f"could not find host {parts.hostname!r}") from error
    if not addresses or any(is_blocked(a) for a in addresses):
        raise ToolError(f"refused {parts.hostname!r}: not a public internet address")
    return addresses


# The request for `url` pinned to `address`: (URL with the IP, Host header, extensions).
def pinned(url: str, address: str) -> tuple[str, str, dict]:
    parts = urlsplit(url)
    port = f":{parts.port}" if parts.port else ""
    ip = f"[{address}]" if ":" in address else address
    name = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
    ip_url = urlunsplit((parts.scheme, ip + port, parts.path or "/", parts.query, ""))
    tls = {"sni_hostname": parts.hostname} if parts.scheme == "https" else {}
    return ip_url, name + port, tls


# GET `url`, following redirects by hand and checking every hop; each request
# goes to the first checked address of its host (pinned).
# Returns (final url, content type, body cut to max_bytes).
def fetch(client: httpx.Client, url: str, settings: ResearchConfig,
          resolve: Callable[[str], list[str]]) -> tuple[str, str, bytes]:
    for _ in range(settings.max_redirects + 1):
        ip_url, host, tls = pinned(url, check_url(url, resolve)[0])
        with client.stream("GET", ip_url, headers={"Host": host}, extensions=tls,
                           follow_redirects=False) as response:
            if response.status_code in REDIRECTS and "location" in response.headers:
                url = urljoin(url, response.headers["location"])
                continue
            if response.status_code != 200:
                raise ToolError(f"page returned HTTP {response.status_code}")
            body = b""
            for chunk in response.iter_bytes():
                body += chunk
                if len(body) >= settings.max_page_bytes:
                    break
            return url, response.headers.get("content-type", ""), body[:settings.max_page_bytes]
    raise ToolError(f"too many redirects (more than {settings.max_redirects})")


# DuckDuckGo text search; returns dicts with title, href and body.
def ddgs_search(query: str, max_results: int) -> list[dict]:
    return DDGS().text(query, region="in-en", max_results=max_results)


# Build the two web tool functions, keyed by name. `client`, `search` and
# `resolve` are passed in so tests can use fakes and never touch the network.
def web_functions(client: httpx.Client, settings: ResearchConfig,
                  search: Callable[[str, int], list[dict]] = ddgs_search,
                  resolve: Callable[[str], list[str]] = resolve_host) -> dict:
    # Search and return each result's url plus its wrapped title and snippet.
    def web_search(args: WebSearchArgs) -> dict:
        try:
            hits = search(args.query, args.max_results)
        except DDGSException as error:
            raise ToolError(f"web search failed: {type(error).__name__}") from error
        results = [{"url": hit.get("href", ""),
                    "text": wrap_untrusted(f"{hit.get('title', '')}\n{hit.get('body', '')}",
                                           hit.get("href", SEARCH_SOURCE))}
                   for hit in hits[: args.max_results]]
        return {"source": SEARCH_SOURCE, "results": results}

    # Fetch one public page and return its main text, wrapped and cut to length.
    def read_page(args: ReadPageArgs) -> dict:
        try:
            url, content_type, body = fetch(client, args.url, settings, resolve)
        except httpx.HTTPError as error:
            raise ToolError(f"could not fetch the page: {type(error).__name__}") from error
        if "html" not in content_type and "text/plain" not in content_type:
            raise ToolError(f"not a web page (content type {content_type or 'unknown'!r})")
        text = trafilatura.extract(body.decode("utf-8", errors="replace"), url=url)
        if not text:
            raise ToolError("no readable text found on the page")
        cut = len(text) > settings.max_page_chars
        return {"url": url, "truncated": cut,
                "text": wrap_untrusted(text[: settings.max_page_chars], url)}

    return {"web_search": web_search, "read_page": read_page}
