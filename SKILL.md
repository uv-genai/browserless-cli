---
name: browserless-cli
description: Use the browserless-cli tool to fetch, scrape, and render web pages via a local or remote Browserless instance. Supports screenshot, PDF, markdown, HTML, structured data extraction, link extraction, and more. Trigger on requests to "fetch a page", "scrape a website", "take a screenshot", "generate a PDF", "render a page", "extract links", or any task requiring a headless browser.
version: 1.1.0
last_updated: 2026-07-07
---

# Browserless CLI

A single Python script that wraps all Browserless REST API endpoints as command-line subcommands. Zero external dependencies beyond Python's standard library.

## Tool

```bash
python3 browserless-cli.py [global-options] <command> [command-options]
```

## Global Options

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `--url URL`, `-u URL` | `BROWSERLESS_URL` | Browserless server URL (default: `https://production-sfo.browserless.io`) |
| `--token TOKEN`, `-t TOKEN` | `BROWSERLESS_TOKEN` | API authentication token |
| `--output FILE`, `-o FILE` | — | Write output to FILE instead of stdout (use `-` for stdout) |

## Commands

### `content` — Fully Rendered HTML

Fetches a page and returns the fully rendered HTML after JavaScript execution.

```bash
python3 browserless-cli.py --url http://localhost:4321 content https://example.com
python3 browserless-cli.py --url http://localhost:4321 --output page.html content https://example.com
```

**Options:**
- `--wait-until` — Wait condition: `domcontentloaded`, `load`, `networkidle0`, `networkidle2`
- `--delay` — Additional milliseconds to wait after the wait condition
- `--headers` — Extra HTTP headers as a JSON object (e.g. `--headers '{"Cookie":"foo=bar"}'`)
- `--extra-args` — Comma-separated extra Chrome CLI args

---

### `scrape` — Structured Data Extraction

Extracts structured data from a page using CSS selectors. Returns a JSON array.

```bash
python3 browserless-cli.py --url http://localhost:4321 scrape https://example.com \
  --elements '[{"name":"title","selector":"h1","attribute":"text"}]'
```

**Options:**
- `--elements` (required) — JSON array of element descriptors:
  ```json
  [
    {"name": "title", "selector": "h1", "attribute": "text"},
    {"name": "links", "selector": "a", "attribute": "href"}
  ]
  ```
- `--wait-until` — Wait condition before scraping

---

### `smart-scrape` — Auto-Detect Best Format

Intelligently detects page content and returns it in the best format.

```bash
python3 browserless-cli.py --url http://localhost:4321 smart-scrape https://example.com --output-format markdown
python3 browserless-cli.py --url http://localhost:4321 smart-scrape https://example.com --output-format json -o data.json
```

**Options:**
- `--output-format` — Preferred format: `json`, `html`, `text`, `markdown`
- `--wait-until` — Wait condition

---

### `screenshot` — Capture Screenshots

Captures screenshots in PNG format.

```bash
python3 browserless-cli.py --url http://localhost:4321 --output page.png screenshot https://example.com
```

**Options:**
- `--type` — Image format: `png` (default), `jpeg`, `webp`
- `--full-page` — Capture the entire scrollable page
- `--quality` — JPEG/WebP quality (1–100)
- `--width` — Viewport width
- `--height` — Viewport height
- `--delay` — Additional ms to wait
- `--clip` — Clip rectangle as JSON: `{"x":0,"y":0,"width":800,"height":600}`

---

### `pdf` — Generate PDFs

Converts a web page to PDF with full print options.

```bash
python3 browserless-cli.py --url http://localhost:4321 --output page.pdf pdf https://example.com
```

**Options:**
- `--landscape` — Landscape orientation
- `--paper-width` — Paper width in inches
- `--paper-height` — Paper height in inches
- `--margin` — Margins as JSON: `{"top":10,"right":10,"bottom":10,"left":10}`
- `--display-header-footer` — Display header and footer
- `--header-template` — HTML template for header
- `--footer-template` — HTML template for footer
- `--print-background` — Print background graphics and colors
- `--scale` — Page scale (0.1–2.0)
- `--delay` — Additional ms to wait

---

### `markdown` — Render as Markdown

Renders a page and saves it as clean Markdown text. Uses the `/content` endpoint and performs local HTML-to-Markdown conversion.

```bash
python3 browserless-cli.py --url http://localhost:4321 --output page.md markdown https://example.com
```

**Options:**
- `--wait-until` — Wait condition (same as `content`)
- `--delay` — Additional ms to wait
- `--headers` — Extra HTTP headers as JSON object

---

### `links` — Extract All Links

Fetches a page and extracts all `<a>` links as a JSON array of `{text, url}` entries. Resolves relative URLs to absolute.

```bash
python3 browserless-cli.py --url http://localhost:4321 links https://example.com
python3 browserless-cli.py --url http://localhost:4321 --output links.json links https://example.com
```

**Options:**
- `--wait-until` — Wait condition: `domcontentloaded`, `load`, `networkidle0`, `networkidle2`
- `--delay` — Additional milliseconds to wait after the wait condition
- `--headers` — Extra HTTP headers as a JSON object (e.g. `--headers '{"Cookie":"foo=bar"}'`)

---

### `search` — Web Search + Scrape

Searches the web and optionally scrapes result pages.

```bash
python3 browserless-cli.py --url http://localhost:4321 search "Python tutorials" --scrape --scrape-options '{"output":"markdown"}'
```

**Options:**
- `--sources` — Comma-separated search sources (e.g. `google,duckduckgo`)
- `--scrape` — Also scrape result pages
- `--scrape-options` — Scrape options as JSON

---

### `map` — Discover Site URLs

Discovers all URLs on a site, optionally preferring the sitemap.

```bash
python3 browserless-cli.py --url http://localhost:4321 map https://example.com
python3 browserless-cli.py --url http://localhost:4321 map https://example.com --sitemap
```

**Options:**
- `--search` — Filter URLs by path pattern
- `--include-subdomains` — Include subdomain URLs
- `--sitemap` — Prefer sitemap.xml over crawling

---

### `function` — Run Custom Puppeteer Code

Executes custom JavaScript code in a browser context. Sends raw JavaScript in the request body.

```bash
python3 browserless-cli.py --url http://localhost:4321 function --code "return document.title;"
python3 browserless-cli.py --url http://localhost:4321 function --code-file extract.js
```

**Options:**
- `--code` — JavaScript code (inline)
- `--code-file` — Path to a `.js` file
- `--context` — Context object to pass to the function (JSON)

---

### `download` — Trigger File Downloads

Runs JavaScript that triggers a file download and captures the file. Sends raw JavaScript in the request body.

```bash
python3 browserless-cli.py --url http://localhost:4321 download --code "window.location.href = '/file.pdf';"
```

**Options:**
- `--code` — JavaScript code (inline)
- `--code-file` — Path to a `.js` file
- `--context` — Context object (JSON)

---

### `export` — Native Content Type Fetch

Fetches a URL and streams the response in its native content type.

```bash
python3 browserless-cli.py --url http://localhost:4321 --output page.html export https://example.com
```

**Options:**
- `--include-resources` — Bundle all resources (CSS, images, JS) into a ZIP
- `--wait-until` — Wait condition
- `--delay` — Additional ms to wait

---

### `unblock` — Bypass Bot Detection

Bypasses bot detection and CAPTCHAs to access protected pages.

```bash
python3 browserless-cli.py --url http://localhost:4321 unblock https://example.com --content --cookies
```

**Options:**
- `--content` — Include rendered HTML in the response
- `--cookies` — Include browser cookies in the response
- `--screenshot` — Include a screenshot in the response
- `--browser-ws-endpoint` — Custom browser WebSocket endpoint

---

### `performance` — Lighthouse Audit

Runs a Lighthouse performance audit.

```bash
python3 browserless-cli.py --url http://localhost:4321 performance https://example.com
python3 browserless-cli.py --url http://localhost:4321 performance https://example.com --categories accessibility,seo
```

**Options:**
- `--categories` — Comma-separated Lighthouse categories: `performance`, `accessibility`, `best-practices`, `seo`, `pwa`
- `--config` — Lighthouse config as JSON
- `--only-categories` — Return only category scores
- `--only-pwa` — Run only PWA audit

---

### `crawl` — Crawl Entire Site

Crawls a site at a given depth and optionally scrapes each page.

```bash
python3 browserless-cli.py --url http://localhost:4321 crawl https://example.com --depth 2 --max-pages 100
```

**Options:**
- `--depth` — Crawl depth (default: `1`)
- `--scrape` — Scrape each page during crawl
- `--scrape-options` — Scrape options as JSON
- `--path-filter` — Comma-separated path filters (e.g. `/blog/,/about/`)
- `--max-pages` — Maximum pages to crawl
- `--delay` — Delay between requests in ms

---

## Configuration

### Using Environment Variables

```bash
export BROWSERLESS_URL=http://localhost:4321
export BROWSERLESS_TOKEN=your-api-token
```

### Using CLI Flags

```bash
python3 browserless-cli.py --url http://localhost:4321 --token mytoken content https://example.com
```

### Precedence

CLI flags override environment variables, which override defaults.

| Setting | Default | Env Var | CLI Flag |
|---------|---------|---------|----------|
| URL | `https://production-sfo.browserless.io` | `BROWSERLESS_URL` | `--url` |
| Token | `""` | `BROWSERLESS_TOKEN` | `--token` |

## Examples

### Extract Links from a Blog

```bash
python3 browserless-cli.py --url http://localhost:4321 --output links.json \
  links https://blog.example.com
```

### Scrape Product Prices

```bash
python3 browserless-cli.py --url http://localhost:4321 scrape https://example.com/shop \
  --elements '[
    {"name":"name","selector":".product-name","attribute":"text"},
    {"name":"price","selector":".price","attribute":"text"}
  ]' --output prices.json
```

### Take a Screenshot of a Dashboard

```bash
python3 browserless-cli.py --url http://localhost:4321 --output dashboard.png \
  screenshot https://dashboard.example.com
```

### Convert Blog Post to Markdown

```bash
python3 browserless-cli.py --url http://localhost:4321 --output blog-post.md \
  markdown https://blog.example.com/post --wait-until networkidle2
```

### Run a Lighthouse SEO Audit

```bash
python3 browserless-cli.py --url http://localhost:4321 --output audit.json \
  performance https://example.com --categories performance,accessibility,seo
```

### Search and Save Results

```bash
python3 browserless-cli.py --url http://localhost:4321 --output search-results.md \
  search "best LLM frameworks 2026" --sources google --scrape \
  --scrape-options '{"output":"markdown"}'
```

## Browserless API Reference

This CLI wraps the following Browserless endpoints:

| Command | API Endpoint | HTTP Method |
|---------|-------------|-------------|
| `content` | `/content` | POST |
| `scrape` | `/scrape` | POST |
| `smart-scrape` | `/smart-scrape` | POST |
| `screenshot` | `/screenshot` | POST |
| `pdf` | `/pdf` | POST |
| `markdown` | `/content` (with local HTML→MD conversion) | POST |
| `links` | `/content` (with local link extraction) | POST |
| `search` | `/search` | POST |
| `map` | `/map` | POST |
| `function` | `/function` | POST |
| `download` | `/download` | POST |
| `export` | `/export` | POST |
| `unblock` | `/unblock` | POST |
| `performance` | `/performance` | POST |
| `crawl` | `/crawl` | POST |

Full API documentation: [https://www.browserless.io/docs/](https://www.browserless.io/docs/)

## Requirements

- **Python 3.8+** (uses `dict[str, ...]` type hints and f-string debugging)
- No pip packages required — pure standard library
- A running Browserless instance (local or remote)

## When to use

- Fetching fully rendered HTML from JavaScript-heavy pages
- Taking screenshots or generating PDFs of web pages
- Extracting structured data with CSS selectors
- Converting pages to clean Markdown
- Extracting all links from a page as JSON
- Running Lighthouse performance audits
- Crawling entire sites for link discovery
- Executing custom Puppeteer/Playwright JavaScript
- Bypassing basic bot detection

## Troubleshooting

**401 Unauthorized:**
```bash
# Check your token
python3 browserless-cli.py --url http://localhost:4321 --token your-token content https://example.com

# Or set via environment variable
export BROWSERLESS_TOKEN=your-token
python3 browserless-cli.py --url http://localhost:4321 content https://example.com
```

**404 Not Found:**
```bash
# Verify the endpoint exists on your Browserless instance
curl -s -X POST "http://localhost:4321/content" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

**400 Bad Request:**
```bash
# Check your JSON payload is valid
python3 browserless-cli.py --url http://localhost:4321 scrape https://example.com \
  --elements '[{"name":"title","selector":"h1","attribute":"text"}]'
```

**Timeout:**
```bash
# Increase timeout for slow-loading pages
python3 browserless-cli.py --url http://localhost:4321 --output page.html \
  content https://example.com --wait-until networkidle2 --delay 5000
```
