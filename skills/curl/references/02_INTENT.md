---
description: When and why to invoke curl, mode selection guide, and chunking strategy.
index:
  - When to Use
  - Mode Selection
  - Chunking Strategy
  - Batch Fetching
---

# Intent

## When to Use

Invoke `curl` when the agent needs to read external content:

- "Summarise this documentation page"
- "What does this API return?"
- "Check the latest version from this JSON endpoint"
- "Fetch these three pages and compare their content"
- "Get the next part of that article" (progressive disclosure)

Do NOT invoke `curl` for local file reading (`ls`, `grep`, `find` serve that
purpose) or for content already in context.

## Mode Selection

| Content type | Recommended mode | Why |
|---|---|---|
| HTML article / docs | `text` | Extracts prose, removes nav/ads |
| HTML with code blocks / tables | `markdown` | Preserves structure as Markdown |
| REST API / JSON endpoint | `json` | Pretty-prints for readability |
| Plain text, CSV, raw bytes | `raw` | No transformation needed |
| Unknown / mixed | `auto` | Detects from Content-Type header |

When uncertain, use `auto`. The kernel inspects the `Content-Type` response
header and routes accordingly:
- `text/html` → `text`
- `application/json` → `json`
- `text/*` → `raw`
- anything else → `raw`

## Chunking Strategy

Start with offset=0 and default length=20000. Read `has_more` in the response:

- `has_more=false` → you have the complete content. Stop.
- `has_more=true` → more content exists. Use `next_offset` as the next offset.

Decide how much to read based on the task, not automatically. If the first
chunk contains sufficient information to answer the question, stop — do not
fetch further chunks unnecessarily.

Adjust `length` to control token budget:
- Smaller `length` (e.g. 5000) for quick previews
- Larger `length` (e.g. 50000) for dense technical content

## Batch Fetching

Multiple URLs can be fetched in a single plan call:

```json
{"urls": ["https://example.com/a", "https://example.com/b"], "mode": "auto"}
```

All URLs use the same `offset` and `length`. For different offsets per URL,
issue separate single-URL plans.

Batch results include a `summary` block and a `results` array. Single-URL
results are returned flat (no wrapping `results` array).
