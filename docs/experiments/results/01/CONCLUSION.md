# Conclusion

## Summary

A experiment was conducted to measure the impact of AUx skills on token consumption and context relevance. Initial results show promise, with 56% reduction in tool calls and 45% less context consumed for equivalent coverage. Multiple areas of improvement are identified, including skill adoption by the agent, output modes, and heuristic guidance.

Re-architecture and improved skill discovery are targeted for future experiments and ongoing.

## What Worked

- **Tool call efficiency:** 56% reduction in tool calls with skills enabled
- **Context savings:** 45% less context consumed for equivalent coverage
- **Search consolidation:** 74% fewer grep operations needed

## Caveats

- Same model used (GPT-5.2) — valid A/B comparison
- Agent used `grep_search` (IDE tool) 7× but skill only 1× — partial adoption
- Skill output verbosity may offset some token savings

## Improvement Opportunities

1. **Skill adoption:** Agent defaulted to IDE grep; better discoverability needed
2. **Output modes:** Configurable summary vs detailed output to reduce follow-up reads
3. **Heuristic guidance:** Skills could suggest entry points, not just matches
