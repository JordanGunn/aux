# curl

> **Agent-optimised HTTP fetch with progressive disclosure**

## Overview

The `curl` skill performs HTTP retrieval and returns clean, bounded content
optimised for agent consumption. Raw HTML, scripts, navigation, and ads are
stripped before content reaches the agent's context. JSON responses are
pretty-printed. Long responses are chunked — the agent requests successive
chunks using `offset` and `length`.

The skill has two distinct code paths:

| Path | Modes | Processing |
|---|---|---|
| HTML | `text`, `markdown` | trafilatura → html2text → stdlib fallback |
| JSON/API | `json` | `json.loads` → `json.dumps(indent=2)` |
| Passthrough | `raw` | no transformation |

Auto-detection (`auto`, default) routes based on the `Content-Type` header.

## When to Use

- "Summarise this documentation page"
- "What does this API endpoint return?"
- "Fetch the latest version from this JSON feed"
- "Get the full content of this article" (progressive disclosure)
- "Fetch these three pages in parallel"

## Key Capabilities

- **Content extraction** — HTML cleaned to plain text or Markdown before agent sees it
- **Progressive disclosure** — `offset`/`length`/`has_more`/`next_offset` per response
- **Batch support** — multiple URLs fetched in parallel in a single plan call
- **Degradation** — graceful fallback chain if optional packages are absent
- **No ceiling** — agent controls depth; default chunk is 20,000 chars (~5k tokens)

## Quick Start

```bash
# Schema (source of truth)
aux curl --schema

# Simple: auto mode, first chunk
aux curl https://docs.python.org/3/library/re.html

# Explicit text extraction
aux curl https://docs.python.org/3/library/re.html --mode text

# Next chunk (progressive disclosure)
aux curl https://docs.python.org/3/library/re.html --mode text --offset 20000

# JSON API
aux curl https://httpbin.org/json --mode json

# Plan mode
aux curl --plan '{"urls":["https://example.com"],"mode":"text","offset":0,"length":20000}'
```

## Progressive Disclosure Loop

```
Step 1: Fetch offset=0. Read has_more.
        If has_more=false → done. Full content retrieved.

Step 2: If more content needed, fetch with offset=next_offset.

Step 3: Stop when has_more=false OR content is sufficient to answer the question.
```

## Output Format

**Single URL:**

```json
{
  "url": "https://...",
  "status": 200,
  "content_type": "text/html; charset=utf-8",
  "mode": "text",
  "offset": 0,
  "length": 20000,
  "chars_returned": 20000,
  "total_chars": 52140,
  "has_more": true,
  "next_offset": 20000,
  "content": "...",
  "error": null
}
```

**Batch (multiple URLs):**

```json
{
  "summary": {"total": 3, "success": 2, "errors": 1},
  "results": [ ... ]
}
```

## Plan Schema

```bash
aux curl --schema
```

Key fields:

| Field | Type | Default | Description |
|---|---|---|---|
| `urls` | `list[str]` | — | URLs to fetch (min 1) |
| `method` | `GET\|POST\|...` | `GET` | HTTP method |
| `headers` | `dict` | `{}` | Request headers |
| `body` | `str\|null` | `null` | Request body (POST/PUT/PATCH only) |
| `mode` | `auto\|text\|markdown\|json\|raw` | `auto` | Extraction mode |
| `offset` | `int ≥ 0` | `0` | Character offset |
| `length` | `int ≥ 100` | `20000` | Characters to return |
| `timeout` | `float` | `30.0` | Request timeout (seconds) |
| `follow_redirects` | `bool` | `true` | Follow HTTP redirects |

## Dependencies

Install optional curl dependencies:

```bash
pip install 'aux-skills[curl]'
```

| Package | Role | Fallback |
|---|---|---|
| `httpx` | HTTP client | Required — curl fails without it |
| `trafilatura` | HTML → clean text | html2text or stdlib |
| `html2text` | HTML → Markdown | stdlib tag-stripping |

Check status:

```bash
aux doctor
```

## Mode Selection Guide

| Content | Mode |
|---|---|
| Documentation, articles, blogs | `text` |
| Content with code blocks / tables | `markdown` |
| REST APIs, JSON endpoints | `json` |
| Plain text, CSV, binary | `raw` |
| Unknown | `auto` |

## Skill Layer

```bash
# Onboard (read all references)
bash skills/curl/scripts/skill.sh init

# Validate dependencies
bash skills/curl/scripts/skill.sh validate

# Schema
bash skills/curl/scripts/skill.sh schema

# Run via stdin plan
echo '{"urls":["https://httpbin.org/json"],"mode":"json"}' \
  | bash skills/curl/scripts/skill.sh run --stdin
```
