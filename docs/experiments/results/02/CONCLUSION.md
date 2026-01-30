# Conclusion

## Summary

Experiment 02 tested the improved skill documentation after architecture cleanup. The rerun achieved **25% context consumption** (97.9k of 384k) while maintaining excellent coverage. This is **-22 percentage points** vs baseline context usage (47% → 25%), and a **46% reduction** in tokens consumed (182.3k → 97.9k).

## What Worked

- **Search-before-read discipline:** Agent followed `/grep` skill protocol consistently
- **Broad → narrow strategy:** broad keyword passes, then scoped passes
- **CLI schema as source of truth:** No confusion from outdated v2 schema docs
- **Producers vs consumers framing:** Clear mental model for auth analysis

## What Changed Since Experiment 01

1. **Deleted orphaned assets:** 36 static schema/template files removed
2. **Updated skill docs:** All references now point to `aux <skill> --schema`
3. **Fixed wrapper scripts:** Help text matches actual CLI interface

## Remaining Observations

- **Skill adoption still low:** Agent used IDE `grep_search` alongside skill
- **Context overhead:** Skill JSON output is verbose; summary mode would help
- **No `--format` flag:** CLI outputs JSON only; agents may prefer condensed output

Note: Reported tool call counts for this rerun exclude `run_command` used to invoke `/grep`.

## Recommendations

1. Add `--format summary` or `--compact` flag to reduce output verbosity
2. Consider IDE integration hints to prefer skill over native `grep_search`
3. Track skill invocation rate as adoption metric in future experiments
