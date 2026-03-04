---
description: Always/Never guardrails for the aux meta-skill.
index:
  - Always
  - Never
  - Chain Length Limit
---

# Policies

## Always

- **Schema first.** After selecting a skill from the registry, run `aux <skill> --schema`
  before constructing a plan. The registry's `requires` field is a hint only; the schema
  is authoritative.

- **Dry-run before apply.** Write skills (`mutates: true`) — `replace` and `rename` —
  must always be run without `--apply` first. Inspect the dry-run output before proceeding.

- **Report the routing decision.** When `/aux` is used to select a skill, tell the user
  which skill was selected and why before executing it.

- **Treat absence as data.** If `aux capabilities` returns a skill list that does not
  contain a skill matching the task, report that gap to the user rather than improvising.

## Never

- **Never use `/aux` as the default interface for every task.** It is for bootstrap and
  ambiguous-intent cases only. Direct skill invocation is always preferred when the
  correct skill is known.

- **Never act on `prune` candidates without `usages` verification.** `prune` output is
  advisory static analysis. Every candidate must be verified with `usages` before deletion.

- **Never apply write operations without reviewing dry-run output.** `--apply` is
  irreversible without a backup. Always confirm with the user.

- **Never construct a plan without first fetching the skill's schema.** Field names can
  change between versions. The registry's `schema_cmd` field gives the exact command.

## Chain Length Limit

Keep skill chains to **at most 3 skills** in a single agent turn. Longer chains should
be broken into separately confirmed steps so the user can review intermediate output.

Example of a 3-skill chain (acceptable in one turn):
```
prune → usages → replace (dry-run only)
```

The apply step of `replace` is a 4th action and requires explicit user confirmation
before executing.
