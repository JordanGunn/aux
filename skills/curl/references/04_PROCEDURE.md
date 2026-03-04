---
description: Step-by-step execution flow including progressive disclosure loop.
index:
  - Step 1: Get schema
  - Step 2: Build plan
  - Step 3: Fetch first chunk
  - Step 4: Read result
  - Step 5: Continue if needed
  - CLI Reference
  - Output Format
---

# Procedure

## Step 1: Get schema

Always retrieve the current schema before constructing a plan:

```bash
bash scripts/skill.sh schema
# or: aux curl --schema
```

The schema is the source of truth for field names, types, and defaults.

## Step 2: Build plan

Construct a JSON plan matching the schema. Minimum required field: `urls`.

```json
{
  "urls": ["https://docs.python.org/3/library/re.html"],
  "mode": "text",
  "offset": 0,
  "length": 20000
}
```

Choose `mode` based on the content type (see 02_INTENT.md — Mode Selection).

## Step 3: Fetch first chunk

```bash
echo '{"urls":["https://..."],"mode":"text"}' \
  | bash scripts/skill.sh run --stdin
```

Or via simple mode:

```bash
bash scripts/skill.sh run https://docs.python.org/3/library/re.html --mode text
```

## Step 4: Read result

Check these fields in the response:

| Field | Meaning |
|---|---|
| `error` | null = success; string = something went wrong |
| `status` | HTTP status code (≥400 = server error) |
| `has_more` | true = more content available beyond this chunk |
| `next_offset` | Offset to use for the next chunk (null if has_more=false) |
| `chars_returned` | Characters in this chunk |
| `total_chars` | Total characters in the extracted content |
| `content` | The actual text/markdown/JSON content |

## Step 5: Continue if needed

**Progressive disclosure loop:**

```
Step 5a: Read has_more.
         If has_more=false → done. Full content retrieved.

Step 5b: Decide: does the current content answer the question?
         If yes → stop. Do not fetch more.
         If no  → fetch next chunk using next_offset.

Step 5c: Repeat from Step 4.
```

Example — fetching the second chunk:

```json
{
  "urls": ["https://docs.python.org/3/library/re.html"],
  "mode": "text",
  "offset": 20000,
  "length": 20000
}
```

## CLI Reference

**Schema:**
```bash
bash scripts/skill.sh schema
```

**Validate dependencies:**
```bash
bash scripts/skill.sh validate
```

**Simple mode:**
```bash
bash scripts/skill.sh run https://example.com --mode text
bash scripts/skill.sh run https://api.example.com/data --mode json
bash scripts/skill.sh run https://example.com --offset 20000
```

**Plan mode (stdin):**
```bash
cat <<'JSON' | bash scripts/skill.sh run --stdin
{
  "urls": ["https://example.com"],
  "mode": "auto",
  "offset": 0,
  "length": 20000
}
JSON
```

**Batch:**
```bash
cat <<'JSON' | bash scripts/skill.sh run --stdin
{
  "urls": ["https://example.com/a", "https://example.com/b"],
  "mode": "text"
}
JSON
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
  "summary": {"total": 2, "success": 2, "errors": 0},
  "results": [ ... ]
}
```
