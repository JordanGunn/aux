---
description: Identity and scope of the rename skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

rename is a single-purpose skill: move or rename a file or directory from one path to another on the filesystem.

It wraps `shutil.move` with a mandatory dry-run gate, conflict detection, and optional backup. It replaces the three-step read-write-delete pattern agents otherwise use to rename files.

## Scope

rename answers: "if I move these paths, will anything go wrong?" It produces a preview for review, then applies on explicit instruction.

It does not handle:
- Content modification (use `aux replace` or `aux sed` for that)
- Creating missing parent directories (that is a scope violation)
- Parallel/concurrent moves (sequential only to avoid fs races)

## Constraints

- No parent creation: if `dst.parent` does not exist, it is an error
- No silent overwrites: `dst` existing without `overwrite: true` is a conflict
- Two phases are mandatory: dry-run first, then apply
- Deterministic: same plan always produces same preview and plan_hash
- Sequential execution: moves process in declaration order
