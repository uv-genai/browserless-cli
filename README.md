# Browserless CLI

A single Python script that wraps **all Browserless REST API endpoints** as command-line subcommands. No external dependencies beyond Python's standard library.

## Features

- **Zero dependencies** — uses only Python's built-in `urllib`, `json`, `argparse`
- **15 commands** covering the full Browserless API surface
- **Configurable** via CLI flags or environment variables
- **Binary-safe output** — handles text and binary responses (images, PDFs)
- **Pipe-friendly** — defaults to stdout for shell scripting

## Quick Start

```bash
# Set up authentication
export BROWSERLESS_URL=https://production-sfo.browserless.io
export BROWSERLESS_TOKEN=your-api-token

# Get the rendered HTML of a page
python3 browserless-cli.py content https://example.com

# Take a screenshot
python3 browserless-cli.py screenshot https://example.com -o page.png

# Generate a PDF
python3 browserless-cli.py pdf https://example.com -o page.pdf
```

## Global Options

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `--url URL`, `-u URL` | `BROWSERLESS_URL` | Browserless server URL (default: `https://production-sfo.browserless.io`) |
| `--token TOKEN`, `-t TOKEN` | `BROWSERLESS_TOKEN` | API authentication token |
| `--output FILE`, `-o FILE` | — | Write output to FILE instead of stdout (use `-` for stdout) |

## Commands

### `content` — Fully Rendered HTML

Fetches a page and returns the **fully rendered HTML** after JavaScript execution.

```bash
python3 browserless-cli.py content https://example.com
python3 browserless-cli.py content https://example.com -o page.html --wait-until networkidle2
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
python3 browserless-cli.py scrape https://example.com \
  --elements '[{"name":"title","selector":"h1","attribute":"text"}]' \
  -o results.json
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
python3 browserless-cli.py smart-scrape https://example.com --output-format markdown
python3 browserless-cli.py smart-scrape https://example.com --output-format json -o data.json
```

**Options:**
- `--output-format` — Preferred format: `json`, `html`, `text`, `markdown`
- `--wait-until` — Wait condition

---

### `screenshot` — Capture Screenshots

Captures screenshots in PNG format.

```bash
python3 browserless-cli.py screenshot https://example.com -o page.png
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
python3 browserless-cli.py pdf https://example.com -o page.pdf
python3 browserless-cli.py pdf https://example.com -o report.pdf \
  --landscape --print-background --delay 2000
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
python3 browserless-cli.py markdown https://example.com -o page.md
```

**Options:**
- `--wait-until` — Wait condition (same as `content`)
- `--delay` — Additional ms to wait
- `--headers` — Extra HTTP headers as JSON object

---

### `search` — Web Search + Scrape

Searches the web and optionally scrapes result pages.

```bash
python3 browserless-cli.py search "Python tutorials" --scrape --scrape-options '{"output":"markdown"}' -o results.json
```

**Options:**
- `--sources` — Comma-separated search sources (e.g. `google,duckduckgo`)
- `--scrape` — Also scrape result pages
- `--scrape-options` — Scrape options as JSON

---

### `map` — Discover Site URLs

Discovers all URLs on a site, optionally preferring the sitemap.

```bash
python3 browserless-cli.py map https://example.com
python3 browserless-cli.py map https://example.com --sitemap
python3 browserless-cli.py map https://example.com --search "/blog/"
```

**Options:**
- `--search` — Filter URLs by path pattern
- `--include-subdomains` — Include subdomain URLs
- `--sitemap` — Prefer sitemap.xml over crawling

---

### `links` — Extract All Links

Fetches a page and extracts all `<a>` links as a JSON array of `{text, url}` entries. Resolves relative URLs to absolute.

```bash
python3 browserless-cli.py links https://example.com
python3 browserless-cli.py links https://example.com -o links.json
```

**Options:**
- `--wait-until` — Wait condition: `domcontentloaded`, `load`, `networkidle0`, `networkidle2`
- `--delay` — Additional milliseconds to wait after the wait condition
- `--headers` — Extra HTTP headers as a JSON object (e.g. `--headers '{"Cookie":"foo=bar"}'`)

---

### `function` — Run Custom Puppeteer Code

Executes custom JavaScript code in a browser context. Sends raw JavaScript in the request body.

```bash
# Inline code
python3 browserless-cli.py function --code "return document.title;"

# From file
python3 browserless-cli.py function --code-file extract.js

# With context object
python3 browserless-cli.py function --code "return page.url();" --context '{"foo":"bar"}'
```

**Options:**
- `--code` — JavaScript code (inline)
- `--code-file` — Path to a `.js` file
- `--context` — Context object to pass to the function (JSON)

---

### `download` — Trigger File Downloads

Runs JavaScript that triggers a file download and captures the file. Sends raw JavaScript in the request body.

```bash
python3 browserless-cli.py download --code-file download.js
python3 browserless-cli.py download --code "window.location.href = '/file.pdf';"
```

**Options:**
- `--code` — JavaScript code (inline)
- `--code-file` — Path to a `.js` file
- `--context` — Context object (JSON)

---

### `export` — Native Content Type Fetch

Fetches a URL and streams the response in its native content type.

```bash
python3 browserless-cli.py export https://example.com -o page.html
python3 browserless-cli.py export https://example.com -o bundle.zip --include-resources
```

**Options:**
- `--include-resources` — Bundle all resources (CSS, images, JS) into a ZIP
- `--wait-until` — Wait condition
- `--delay` — Additional ms to wait

---

### `unblock` — Bypass Bot Detection

Bypasses bot detection and CAPTCHAs to access protected pages.

```bash
python3 browserless-cli.py unblock https://example.com -o page.html --content --cookies
python3 browserless-cli.py unblock https://example.com --content --screenshot
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
python3 browserless-cli.py performance https://example.com
python3 browserless-cli.py performance https://example.com --categories accessibility,seo
python3 browserless-cli.py performance https://example.com --only-pwa
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
python3 browserless-cli.py crawl https://example.com --depth 2 --scrape --max-pages 100
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
export BROWSERLESS_URL=https://production-sfo.browserless.io
export BROWSERLESS_TOKEN=abc123xyz
```

### Using CLI Flags

```bash
python3 browserless-cli.py --url https://my-browserless.io --token mytoken content https://example.com
```

### Precedence

CLI flags override environment variables, which override defaults.

| Setting | Default | Env Var | CLI Flag |
|---------|---------|---------|----------|
| URL | `https://production-sfo.browserless.io` | `BROWSERLESS_URL` | `--url` |
| Token | `""` | `BROWSERLESS_TOKEN` | `--token` |

---

## Examples

### Scrape Product Prices

```bash
python3 browserless-cli.py scrape https://example.com/shop \
  --elements '[
    {"name":"name","selector":".product-name","attribute":"text"},
    {"name":"price","selector":".price","attribute":"text"}
  ]' -o prices.json
```

### Take a Screenshot of a Dashboard

```bash
python3 browserless-cli.py screenshot https://dashboard.example.com \
  -o dashboard.png
```

### Convert Blog Post to Markdown

```bash
python3 browserless-cli.py markdown https://blog.example.com/post \
  -o blog-post.md --wait-until networkidle2
```

### Run a Lighthouse SEO Audit

```bash
python3 browserless-cli.py performance https://example.com \
  --categories performance,accessibility,seo -o audit.json
```

### Extract Links from a Blog

```bash
python3 browserless-cli.py links https://blog.example.com -o links.json
```

### Search and Save Results

```bash
python3 browserless-cli.py search "best LLM frameworks 2026" \
  --sources google \
  --scrape \
  --scrape-options '{"output":"markdown"}' \
  -o search-results.md
```

---

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
| `search` | `/search` | POST |
| `map` | `/map` | POST |
| `function` | `/function` | POST |
| `download` | `/download` | POST |
| `export` | `/export` | POST |
| `unblock` | `/unblock` | POST |
| `performance` | `/performance` | POST |
| `crawl` | `/crawl` | POST |
| `links` | `/content` (with local link extraction) | POST |

Full API documentation: [https://www.browserless.io/docs/](https://www.browserless.io/docs/)

---

## Requirements

- **Python 3.8+** (uses `dict[str, ...]` type hints and f-string debugging)
- No pip packages required — pure standard library

## License

MIT
