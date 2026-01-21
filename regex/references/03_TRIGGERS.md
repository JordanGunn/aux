---
description: When this skill activates.
index:
  - Activation
  - Examples
---

# Triggers

## Activation

This skill activates when the user invokes `/regex` followed by a natural language prompt describing what pattern they want to match or extract.

## Examples

- `/regex extract all email addresses from this text`
- `/regex find phone numbers in US format`
- `/regex match all URLs in the document`
- `/regex extract version numbers like v1.2.3`
- `/regex find all IP addresses`
- `/regex match dates in ISO format`

The prompt is treated as intent. The agent compiles it into an explicit regex pattern.
