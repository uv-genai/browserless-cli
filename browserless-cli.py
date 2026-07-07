#!/usr/bin/env python3
"""
Universal Browserless CLI wrapper — a single script that exposes every
Browserless REST API endpoint as a subcommand.

Usage:
    BROWSERLESS_URL=... BROWSERLESS_TOKEN=... python browserless-cli.py <command> [args]

The URL defaults to https://production-sfo.browserless.io
The token defaults to the env var BROWSERLESS_TOKEN or CLI --token flag.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_URL = "https://production-sfo.browserless.io"
USAGE = f"""\\
Usage: browserless-cli [global options] <command> [options]

Global options:
  --url URL, -u URL      Browserless server URL (default: env BROWSERLESS_URL or {DEFAULT_URL})
  --token TOKEN, -t TOKEN   API token (default: env BROWSERLESS_TOKEN)
  --output FILE, -o FILE  Write output to FILE instead of stdout (use - for stdout)

Commands:
  content       Render a page and return fully rendered HTML (includes JS)
  scrape        Extract structured data using CSS selectors
  smart-scrape  Auto-detect page content and return best format (json/html)
  screenshot    Capture a screenshot (PNG/JPEG/WebP)
  pdf           Generate a PDF from a page
  search        Search the web and optionally scrape result pages
  map           Discover URLs on a site or sitemap
  function      Run custom Puppeteer code
  download      Download files triggered during browser execution
  export        Fetch a URL and stream it in native content type
  unblock       Bypass bot detection / CAPTCHAs
  performance   Run Lighthouse audit (SEO, accessibility, speed)
  crawl         Crawl an entire site and scrape every page
  markdown      Render a page and save as Markdown
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_config(args):
    """Resolve Browserless server URL and token from CLI flags or env vars."""
    url = getattr(args, "url", None) or os.environ.get("BROWSERLESS_URL", DEFAULT_URL)
    token = getattr(args, "token", None) or os.environ.get("BROWSERLESS_TOKEN", "")
    out = getattr(args, "output", None) or "-"
    return url.rstrip("/"), token, out


def build_url(base_url: str, endpoint: str, params: dict) -> str:
    """Build a URL with query params (token always included)."""
    if params:
        return f"{base_url}/{endpoint}?{urlencode(params)}"
    return f"{base_url}/{endpoint}"


def build_url_no_params(base_url: str, endpoint: str, token: str) -> str:
    if token:
        return f"{base_url}/{endpoint}?token={token}"
    return f"{base_url}/{endpoint}"


def post_json(base_url: str, endpoint: str, token: str, payload: dict,
              content_type: str = "application/json") -> tuple[bytes | str, str, dict]:
    """POST JSON, return (body_bytes_or_str, content_type, headers)."""
    url = build_url_no_params(base_url, endpoint, token)
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", content_type)
    req.add_header("User-Agent", "browserless-cli/1.0")

    with urlopen(req, timeout=120) as resp:
        body = resp.read()
        ct = resp.headers.get("Content-Type", "application/octet-stream")
        return body, ct, dict(resp.headers)


def post_raw(base_url: str, endpoint: str, token: str, raw_js: str) -> tuple[bytes, str]:
    """POST raw JavaScript, return (body_bytes, content_type)."""
    url = build_url_no_params(base_url, endpoint, token)
    req = Request(url, data=raw_js.encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/javascript")
    req.add_header("User-Agent", "browserless-cli/1.0")

    with urlopen(req, timeout=120) as resp:
        body = resp.read()
        ct = resp.headers.get("Content-Type", "application/javascript")
        return body, ct


def write_output(body: bytes | str, out: str):
    """Write body to file or stdout."""
    if out == "-":
        sys.stdout.buffer.write(body) if isinstance(body, bytes) else sys.stdout.write(str(body))
    else:
        with open(out, "wb" if isinstance(body, bytes) else "w") as f:
            f.write(body)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_content(args):
    """Render a page and return fully rendered HTML."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url}
    if args.wait_until:
        payload["waitUntil"] = args.wait_until
    if args.delay:
        payload["delay"] = args.delay
    if args.headers:
        payload["headers"] = json.loads(args.headers)
    if args.extra_args:
        payload["extra_args"] = args.extra_args.split(",")
    body, ct, _ = post_json(base_url, "content", token, payload)
    write_output(body, out)
    print(f"\nSaved content ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_scrape(args):
    """Extract structured data using CSS selectors."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url, "elements": json.loads(args.elements)}
    if args.wait_until:
        payload["waitUntil"] = args.wait_until
    body, ct, _ = post_json(base_url, "scrape", token, payload)
    write_output(body, out)
    print(f"\nSaved scrape results ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_smart_scrape(args):
    """Auto-detect page content and return best format."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url}
    if args.output_format:
        payload["output"] = args.output_format
    if args.wait_until:
        payload["waitUntil"] = args.wait_until
    body, ct, _ = post_json(base_url, "smart-scrape", token, payload)
    write_output(body, out)
    print(f"\nSaved smart-scrape ({len(body)} bytes) to {out}", file=sys.stderr)


def _html_to_markdown(html: str) -> str:
    """Basic HTML to Markdown conversion."""
    import re
    md = html
    # Remove script and style blocks
    md = re.sub(r'<script[^>]*>.*?</script>', '', md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r'<style[^>]*>.*?</style>', '', md, flags=re.DOTALL | re.IGNORECASE)
    # Convert headings
    def _heading_repl(m):
        level = int(m.group(0)[2])
        return f'\n{"#" * level} {m.group(1)}\n'
    for i in range(6, 0, -1):
        md = re.sub(rf'<h{i}[^>]*>(.*?)</h{i}>', _heading_repl, md, flags=re.IGNORECASE)
    # Convert links
    md = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', md, flags=re.IGNORECASE)
    # Convert bold
    md = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', md, flags=re.IGNORECASE)
    # Convert italic
    md = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', md, flags=re.IGNORECASE)
    # Convert paragraphs
    md = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', md, flags=re.IGNORECASE)
    # Convert line breaks
    md = re.sub(r'<br\s*/?>', '\n', md, flags=re.IGNORECASE)
    # Convert images
    md = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>', r'![\2](\1)', md, flags=re.IGNORECASE)
    md = re.sub(r'<img[^>]*alt="([^"]*)"[^>]*src="([^"]*)"[^>]*>', r'![\1](\2)', md, flags=re.IGNORECASE)
    # Convert unordered lists
    md = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', md, flags=re.IGNORECASE)
    # Convert code blocks
    md = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n', md, flags=re.IGNORECASE)
    md = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', md, flags=re.IGNORECASE)
    # Remove remaining HTML tags
    md = re.sub(r'<[^>]+>', '', md)
    # Clean up whitespace
    md = re.sub(r'\n{3,}', '\n\n', md)
    md = md.strip()
    return md


def cmd_markdown(args):
    """Render a page and save as Markdown."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url}
    if args.wait_until:
        payload["waitUntil"] = args.wait_until
    if args.delay:
        payload["delay"] = args.delay
    if args.headers:
        payload["headers"] = json.loads(args.headers)
    body, ct, _ = post_json(base_url, "content", token, payload)
    # Convert HTML to Markdown
    if isinstance(body, bytes):
        html = body.decode("utf-8")
    else:
        html = body
    md = _html_to_markdown(html)
    write_output(md, out)
    print(f"\nSaved markdown ({len(md)} bytes) to {out}", file=sys.stderr)


def cmd_screenshot(args):
    """Capture a screenshot (PNG/JPEG/WebP)."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url}
    body, ct, _ = post_json(base_url, "screenshot", token, payload)
    write_output(body, out)
    print(f"\nSaved screenshot ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_pdf(args):
    """Generate a PDF from a page."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url}
    if args.landscape:
        payload["landscape"] = True
    if args.paper_width:
        payload["width"] = float(args.paper_width)
    if args.paper_height:
        payload["height"] = float(args.paper_height)
    if args.margin:
        payload["margin"] = json.loads(args.margin)
    if args.display_header_footer:
        payload["displayHeaderFooter"] = True
    if args.header_template:
        payload["headerTemplate"] = args.header_template
    if args.footer_template:
        payload["footerTemplate"] = args.footer_template
    if args.print_background:
        payload["printBackground"] = True
    if args.scale:
        payload["scale"] = float(args.scale)
    if args.delay:
        payload["delay"] = args.delay
    body, ct, _ = post_json(base_url, "pdf", token, payload)
    write_output(body, out)
    print(f"\nSaved PDF ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_search(args):
    """Search the web and optionally scrape result pages."""
    base_url, token, out = get_config(args)
    payload = {"query": args.query}
    if args.sources:
        payload["sources"] = args.sources.split(",")
    if args.scrape:
        payload["scrape"] = True
    if args.scrape_options:
        payload["scrapeOptions"] = json.loads(args.scrape_options)
    body, ct, _ = post_json(base_url, "search", token, payload)
    write_output(body, out)
    print(f"\nSaved search results ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_map(args):
    """Discover URLs on a site or sitemap."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url}
    if args.search:
        payload["search"] = args.search
    if args.include_subdomains:
        payload["includeSubdomains"] = True
    if args.sitemap:
        payload["sitemap"] = True
    body, ct, _ = post_json(base_url, "map", token, payload)
    write_output(body, out)
    print(f"\nSaved map results ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_function(args):
    """Run custom Puppeteer code."""
    base_url, token, out = get_config(args)
    if args.code_file:
        with open(args.code_file) as f:
            code = f.read()
    elif args.code:
        code = args.code
    else:
        print("Error: --code or --code-file is required", file=sys.stderr)
        sys.exit(1)

    body, ct = post_raw(base_url, "function", token, code)
    write_output(body, out)
    print(f"\nSaved function output ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_download(args):
    """Download files triggered during browser execution."""
    base_url, token, out = get_config(args)
    if args.code_file:
        with open(args.code_file) as f:
            code = f.read()
    elif args.code:
        code = args.code
    else:
        print("Error: --code or --code-file is required", file=sys.stderr)
        sys.exit(1)

    body, ct = post_raw(base_url, "download", token, code)
    write_output(body, out)
    print(f"\nSaved download ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_export(args):
    """Fetch a URL and stream it in native content type."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url}
    if args.include_resources:
        payload["includeResources"] = True
    if args.wait_until:
        payload["waitUntil"] = args.wait_until
    if args.delay:
        payload["delay"] = args.delay
    body, ct, _ = post_json(base_url, "export", token, payload)
    write_output(body, out)
    print(f"\nSaved export ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_unblock(args):
    """Bypass bot detection / CAPTCHAs."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url}
    if args.content:
        payload["content"] = True
    if args.cookies:
        payload["cookies"] = True
    if args.screenshot:
        payload["screenshot"] = True
    if args.browser_ws_endpoint:
        payload["browserWSEndpoint"] = args.browser_ws_endpoint
    body, ct, _ = post_json(base_url, "unblock", token, payload)
    write_output(body, out)
    print(f"\nSaved unblock result ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_performance(args):
    """Run Lighthouse audit (SEO, accessibility, speed)."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url}
    if args.categories:
        payload["categories"] = args.categories.split(",")
    if args.config:
        payload["config"] = json.loads(args.config)
    if args.only_categories:
        payload["onlyCategories"] = True
    if args.only_pwa:
        payload["onlyPWA"] = True
    body, ct, _ = post_json(base_url, "performance", token, payload)
    write_output(body, out)
    print(f"\nSaved performance audit ({len(body)} bytes) to {out}", file=sys.stderr)


def cmd_crawl(args):
    """Crawl an entire site and scrape every page."""
    base_url, token, out = get_config(args)
    payload = {"url": args.page_url, "depth": args.depth}
    if args.scrape:
        payload["scrape"] = True
    if args.scrape_options:
        payload["scrapeOptions"] = json.loads(args.scrape_options)
    if args.path_filter:
        payload["pathFilter"] = args.path_filter.split(",")
    if args.max_pages:
        payload["maxPages"] = args.max_pages
    if args.delay:
        payload["delay"] = args.delay
    body, ct, _ = post_json(base_url, "crawl", token, payload)
    write_output(body, out)
    print(f"\nSaved crawl results ({len(body)} bytes) to {out}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser():
    p = argparse.ArgumentParser(
        description="Universal Browserless CLI — exposes all Browserless REST APIs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=USAGE,
    )

    # Global options
    p.add_argument("--url", "-u", help=f"Browserless server URL (default: env BROWSERLESS_URL or {DEFAULT_URL})")
    p.add_argument("--token", "-t", help="API token (default: env BROWSERLESS_TOKEN)")
    p.add_argument("--output", "-o", help="Output file (default: stdout)")

    sub = p.add_subparsers(dest="command", help="Available commands")

    # --- content ---
    sp = sub.add_parser("content", help="Get fully rendered HTML (includes JS)")
    sp.add_argument("page_url", help="URL to fetch")
    sp.add_argument("--wait-until", help="Wait condition (domcontentloaded, load, networkidle0, networkidle2)")
    sp.add_argument("--delay", type=int, help="Additional ms to wait")
    sp.add_argument("--headers", help="Extra headers as JSON object")
    sp.add_argument("--extra-args", help="Comma-separated extra Chrome args")

    # --- scrape ---
    sp = sub.add_parser("scrape", help="Extract structured data with CSS selectors")
    sp.add_argument("page_url", help="URL to scrape")
    sp.add_argument("--elements", required=True, help="JSON array of {selector, ...} elements")
    sp.add_argument("--wait-until", help="Wait condition")

    # --- smart-scrape ---
    sp = sub.add_parser("smart-scrape", help="Auto-detect and return best content format")
    sp.add_argument("page_url", help="URL to scrape")
    sp.add_argument("--output-format", help="Preferred output format: json, html, text, markdown")
    sp.add_argument("--wait-until", help="Wait condition")

    # --- screenshot ---
    sp = sub.add_parser("screenshot", help="Capture a screenshot")
    sp.add_argument("page_url", help="URL to screenshot")

    # --- pdf ---
    sp = sub.add_parser("pdf", help="Generate PDF from a page")
    sp.add_argument("page_url", help="URL to convert")
    sp.add_argument("--landscape", action="store_true", help="Landscape orientation")
    sp.add_argument("--paper-width", type=float, help="Paper width in inches")
    sp.add_argument("--paper-height", type=float, help="Paper height in inches")
    sp.add_argument("--margin", help="Margins as JSON {top,right,bottom,left}")
    sp.add_argument("--header-template", help="HTML template for header")
    sp.add_argument("--footer-template", help="HTML template for footer")
    sp.add_argument("--display-header-footer", action="store_true", help="Display header and footer")
    sp.add_argument("--print-background", action="store_true", help="Print background graphics")
    sp.add_argument("--scale", type=float, help="Page scale (0.1-2.0)")
    sp.add_argument("--delay", type=int, help="Additional ms to wait")

    # --- markdown ---
    sp = sub.add_parser("markdown", help="Render a page and save as Markdown")
    sp.add_argument("page_url", help="URL to convert")
    sp.add_argument("--wait-until", help="Wait condition (domcontentloaded, load, networkidle0, networkidle2)")
    sp.add_argument("--delay", type=int, help="Additional ms to wait")
    sp.add_argument("--headers", help="Extra headers as JSON object")

    # --- search ---
    sp = sub.add_parser("search", help="Search the web and scrape results")
    sp.add_argument("query", help="Search query")
    sp.add_argument("--sources", help="Comma-separated search sources")
    sp.add_argument("--scrape", action="store_true", help="Also scrape result pages")
    sp.add_argument("--scrape-options", help="Scrape options as JSON")

    # --- map ---
    sp = sub.add_parser("map", help="Discover URLs on a site")
    sp.add_argument("page_url", help="Base URL to map")
    sp.add_argument("--search", help="Filter URLs by pattern")
    sp.add_argument("--include-subdomains", action="store_true")
    sp.add_argument("--sitemap", action="store_true", help="Prefer sitemap over crawling")

    # --- function ---
    sp = sub.add_parser("function", help="Run custom Puppeteer code")
    sp.add_argument("--code", help="JavaScript code inline")
    sp.add_argument("--code-file", help="Path to a .js file with the Puppeteer code")
    sp.add_argument("--context", help="Context object to pass to the function as JSON")

    # --- download ---
    sp = sub.add_parser("download", help="Download files triggered during browser execution")
    sp.add_argument("--code", help="JavaScript code inline")
    sp.add_argument("--code-file", help="Path to a .js file with the Puppeteer code")
    sp.add_argument("--context", help="Context object to pass as JSON")

    # --- export ---
    sp = sub.add_parser("export", help="Fetch URL and stream in native content type")
    sp.add_argument("page_url", help="URL to fetch")
    sp.add_argument("--include-resources", action="store_true", help="Bundle resources into a zip")
    sp.add_argument("--wait-until", help="Wait condition")
    sp.add_argument("--delay", type=int, help="Additional ms to wait")

    # --- unblock ---
    sp = sub.add_parser("unblock", help="Bypass bot detection / CAPTCHAs")
    sp.add_argument("page_url", help="URL to unblock")
    sp.add_argument("--content", action="store_true", help="Include rendered HTML")
    sp.add_argument("--cookies", action="store_true", help="Include cookies")
    sp.add_argument("--screenshot", action="store_true", help="Include screenshot")
    sp.add_argument("--browser-ws-endpoint", help="Custom browser WebSocket endpoint")

    # --- performance ---
    sp = sub.add_parser("performance", help="Run Lighthouse audit")
    sp.add_argument("page_url", help="URL to audit")
    sp.add_argument("--categories", help="Comma-separated Lighthouse categories")
    sp.add_argument("--config", help="Lighthouse config as JSON")
    sp.add_argument("--only-categories", action="store_true")
    sp.add_argument("--only-pwa", action="store_true")

    # --- crawl ---
    sp = sub.add_parser("crawl", help="Crawl entire site and scrape pages")
    sp.add_argument("page_url", help="Base URL to crawl")
    sp.add_argument("--depth", type=int, default=1, help="Crawl depth (default: 1)")
    sp.add_argument("--scrape", action="store_true", help="Scrape each page")
    sp.add_argument("--scrape-options", help="Scrape options as JSON")
    sp.add_argument("--path-filter", help="Comma-separated path filters")
    sp.add_argument("--max-pages", type=int, help="Maximum pages to crawl")
    sp.add_argument("--delay", type=int, help="Delay between requests in ms")

    return p


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

COMMANDS = {
    "content": cmd_content,
    "scrape": cmd_scrape,
    "smart-scrape": cmd_smart_scrape,
    "screenshot": cmd_screenshot,
    "pdf": cmd_pdf,
    "markdown": cmd_markdown,
    "search": cmd_search,
    "map": cmd_map,
    "function": cmd_function,
    "download": cmd_download,
    "export": cmd_export,
    "unblock": cmd_unblock,
    "performance": cmd_performance,
    "crawl": cmd_crawl,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        print(USAGE)
        sys.exit(1)

    handler = COMMANDS.get(args.command)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
