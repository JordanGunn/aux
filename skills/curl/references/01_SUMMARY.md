---
description: Identity, scope, two-path design, and progressive disclosure model.
index:
  - Identity
  - Scope
  - Two-Path Design
  - Progressive Disclosure
  - Constraints
---

# Summary

## Identity

`curl` is a single skill that performs agent-optimised HTTP retrieval. It
converts URLs into clean, bounded text — stripping HTML noise, formatting JSON,
and paginating long responses — before content reaches the agent's context.

Raw HTML, scripts, ads, and navigation boilerplate never appear in the output.
The agent reads extracted content, not HTTP responses.

## Scope

`curl` answers "what does this URL contain?" in a form the agent can read
efficiently. It handles:

- Articles, documentation pages, and blog posts (HTML → plain text or Markdown)
- REST APIs and data endpoints (JSON → pretty-printed)
- Plain text resources (returned verbatim)
- Batch retrieval of multiple URLs in parallel

It does not browse the web interactively, handle JavaScript-rendered pages,
manage authentication sessions, or follow pagination links autonomously.

## Two-Path Design

The kernel splits at content type:

**HTML path** (`text`, `markdown` modes)
: Fetches raw HTML → extracts main content via trafilatura (preferred),
  html2text (fallback), or stdlib tag-stripping (emergency fallback).
  Output: clean prose, no navigation or boilerplate.

**JSON/API path** (`json` mode)
: Fetches response body → parses JSON → re-serialises with indent=2.
  On parse failure: returns raw body with a warning in the `error` field.

**Raw path** (`raw` mode)
: No processing. Returns response body verbatim.

**Auto-detection** (`auto` mode, default)
: Inspects `Content-Type` header and routes to the appropriate path.

## Progressive Disclosure

Every response includes position metadata:

```
offset=0,     length=20000 → content[0:20000]     has_more=true,  next_offset=20000
offset=20000, length=20000 → content[20000:40000]  has_more=true,  next_offset=40000
offset=40000, length=20000 → content[40000:52140]  has_more=false, next_offset=null
```

The agent controls depth. Default `length=20000` (~5k tokens). No ceiling
imposed by the system — grow or shrink `length` per request as needed.

## Constraints

- Read-only: no cookies, sessions, or state are persisted between calls.
- Deterministic: same URL + same offset + same length → same chunk.
- Credentials must never appear in plan JSON (headers are logged).
- The skill respects `robots.txt` implicitly through the target server's
  response — it does not enforce crawl policies itself.
