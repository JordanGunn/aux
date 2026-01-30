# Methodology

At a high level, the methodology involves running the same two prompts in two different agent sessions. The only difference between the sessions is the availability of AUx skills, with all other factors remaining constant. A comparison of the resulting metrics will allow us to evaluate the impact of AUx skills on the agent's performance.

## Session A

Native tools only (IDE's built-in grep, file reading)

## Session B

AUx skills enabled (structured grep/find/diff/ls with explicit parameters)

## Session A vs. Session B

Compare the following metrics:

- Tokens used
- Tool calls
- Files read
- Context relevance
- Time to completion

Record all findings.